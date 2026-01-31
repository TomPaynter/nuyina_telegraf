import csv
import re
import sys
import os
from influxdb_client import InfluxDBClient

# --- CONFIGURATION ---
DOCKER_PATH = "../docker-compose.yaml"
DOCKER_PATH = "../docker-compose-main_system.yaml"
MEASUREMENT = "ipms"  # The measurement you want to inspect
OUTPUT_MODE = "print"   # Options: "print" or "csv"
CSV_FILENAME = "measurement_schema.csv"

def get_docker_env_vars(path):
    """Extracts InfluxDB details from docker-compose.yaml environment section."""
    env_vars = {}
    try:
        with open(path, 'r') as f:
            content = f.read()
            # Regex to find key=value even with spaces or hyphens
            matches = re.findall(r'-\s*(INFLUX_[A-Z_]+)\s*=\s*(.*)', content)
            for key, value in matches:
                env_vars[key.strip()] = value.strip()
        
        # Mapping docker env names to what the script expects
        return {
            'url': env_vars.get('INFLUX_URL'),
            'token': env_vars.get('INFLUX_TOKEN'),
            'org': env_vars.get('INFLUX_ORG'),
            'bucket': env_vars.get('INFLUX_BUCKET')
        }
    except Exception as e:
        print(f"Error: Could not read docker-compose at {path}. {e}")
        sys.exit(1)

def run_schema_lookup():
    cfg = get_docker_env_vars(DOCKER_PATH)
    
    # Validation
    if not all([cfg['url'], cfg['token'], cfg['org'], cfg['bucket']]):
        print("Error: Could not find all required INFLUX_ variables in docker-compose.yaml")
        print(f"Found: {cfg}")
        sys.exit(1)

    client = InfluxDBClient(url=cfg['url'], token=cfg['token'], org=cfg['org'])
    query_api = client.query_api()

    # Flux query to determine current field types
    flux_query = f'''
    from(bucket: "{cfg['bucket']}")
      |> range(start: -3000d)
      |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
      |> last()
    '''

    try:
        tables = query_api.query(flux_query)
        fields_found = []
        
        dtype_map = {'float': 'float', 'int': 'integer', 'str': 'string', 'bool': 'boolean'}

        for table in tables:
            for record in table.records:
                f_name = record.get_field()
                f_type = dtype_map.get(type(record.get_value()).__name__, type(record.get_value()).__name__)
                fields_found.append({"field name": f_name, "data type": f_type})

        if not fields_found:
            print(f"No data found for measurement '{MEASUREMENT}' in bucket '{cfg['bucket']}'.")
            return

        if OUTPUT_MODE.lower() == "csv":
            with open(CSV_FILENAME, mode='w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["field name", "data type"])
                writer.writeheader()
                writer.writerows(fields_found)
            print(f"Success! Schema exported to {CSV_FILENAME}")
        else:
            print(f"\nConnected to: {cfg['url']}")
            print(f"Schema for Measurement: {MEASUREMENT}")
            print(f"{'-'*45}")
            print(f"{'FIELD NAME':<32} | {'DATA TYPE':<10}")
            print(f"{'-'*45}")
            for item in sorted(fields_found, key=lambda x: x['field name']):
                print(f"{item['field name']:<32} | {item['data type']:<10}")
            print(f"{'-'*45}\n")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_schema_lookup()
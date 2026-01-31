# nuyina_telegraf

sudo docker exec -it telegraf bash


    telegraf --config /etc/telegraf/telegraf.conf --config-directory /etc/telegraf/telegraf.d --test --debug


 telegraf --config /etc/telegraf/telegraf.conf --config-directory /etc/telegraf/telegraf.d --test --debug | grep "no match found"

 scp /mnt/rvdas/aws430_pfa/aws430_pfa-2026-01-15.txt aadc@172.16.29.8:/home/aadc/nuyina_telegraf/test_data/aws430_pfa

# AI Prompt - Check

This is the data field names and types for two databases, can you please tell me what is different and what is missing. Ours → 172.16.29.8:12345 Theirs → 172.16.29.2:8086

# AI Prompt - Generate

This is a fluentd config, would you please be able to convert it to a telegraf config. I would like the influxdb field and measurement names and data types to remain constant. Please dont combine it to other files already discussed.

The timestamp must be captured in this manner:
^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"}

All fields should be done in optional notation like:
(?:%{NUMBER:roll:float})?

Any fields that are to be ignored should be done like this:
(?:%{NUMBER})?

Any integer must be captured as a float and then converted to an int like:
(?:%{NUMBER:zda_day:float})?

[[processors.converter]]
  namepass = ["seapath_1"]
  [processors.converter.fields]
    integer = ["zda_day"]

For any line that has an * in it, such as an nmea checksum, please ignore all text after the literal * used. Otherwise can you account for for potential white space/eol at the end of each line, like this:
'.*\*.*'

If any lines are ignored, please ignore them by message type, like this:
'^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"},\$(?:GPGSV|GLGSV|GNGSA|GNGRS).*?(\*.*)?'

Do not add a catch all like this, only named messages are to be ignored:
'.*\*.*'

The grok lines need to be single lines, not multi line.

Only use a single backslash for the field delimeters, ie \$PVDRA

Any latitude/longitude fields in a non decimal degree notation, please convert them to a decimal degree and save with a _deg suffix. Please use this starlark processor

[[processors.starlark]]
  namepass = ["seapath_1"]
  source = '''
def apply(metric):
    # Latitude Conversion for INGGA (latitude_1)
    lat_raw = metric.fields.get('latitude_1')
    if lat_raw:
        deg = int(lat_raw / 100)
        min = lat_raw - (deg * 100)
        lat_deg = deg + (min / 60.0)
        if metric.fields.get('n_or_s_1') == "S": lat_deg = -lat_deg
        metric.fields['lat_deg'] = lat_deg

    # Longitude Conversion for INGGA (longitude_1)
    lon_raw = metric.fields.get('longitude_1')
    if lon_raw:
        deg = int(lon_raw / 100)
        min = lon_raw - (deg * 100)
        lon_deg = deg + (min / 60.0)
        if metric.fields.get('e_or_w_1') == "W": lon_deg = -lon_deg
        metric.fields['lon_deg'] = lon_deg

    return metric
'''

This is an example snippet, please follow the syle and formatting.

[[inputs.tail]]
  watch_method = "inotify"
  from_beginning = false
  files = ["/sea_path/seapath_1-*.txt"]
  name_override = "seapath_1"
  data_format = "grok"

grok_patterns = [
    '^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"},\$INZDA,(?:%{NUMBER:zda_time:float})?,(?:%{NUMBER:zda_day:float})?,(?:%{NUMBER:zda_month:float})?,(?:%{NUMBER:zda_year:float})?.*\*.*',
    '^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"},\$INGGA,(?:%{NUMBER:gps_time_1:float})?,(?:%{NUMBER:latitude_1:float})?,(?:%{DATA:n_or_s_1})?,(?:%{NUMBER:longitude_1:float})?,(?:%{DATA:e_or_w_1})?,(?:%{NUMBER:fix_quality_1:float})?,(?:%{NUMBER:num_satellites_1:float})?,(?:%{NUMBER:hdop_1:float})?,(?:%{NUMBER:antenna_height_1:float})?,M?,(?:%{NUMBER:geoid_height_1:float})?,M?,?.*\*.*',
    '^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"},\$INGLL,(?:%{NUMBER:latitude_gll:float})?,(?:%{DATA:n_or_s_gll})?,(?:%{NUMBER:longitude_gll:float})?,(?:%{DATA:e_or_w_gll})?,(?:%{NUMBER:time_gll:float})?,(?:%{DATA:status_gll})?,(?:%{DATA:mode_gll})?.*\*.*',
    '^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"},\$PSXN,23,(?:%{NUMBER:roll:float})?,(?:%{NUMBER:pitch:float})?,(?:%{NUMBER:heading:float})?,(?:%{NUMBER:heave:float})?.*\*.*',
    '^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"},\$PSXN,24,(?:%{NUMBER:roll_rate:float})?,(?:%{NUMBER:pitch_rate:float})?,(?:%{NUMBER:yaw_rate:float})?,(?:%{NUMBER:heave_rate:float})?.*\*.*',
    '^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"},\$INHDT,(?:%{NUMBER:heading_true:float})?,T?.*\*.*',
    '^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"},\$INVTG,(?:%{NUMBER:course_true:float})?,T?,(?:%{NUMBER:course_mag:float})?,M?,(?:%{NUMBER:speed_knots:float})?,N?,(?:%{NUMBER:speed_kmh:float})?,K?,(?:%{DATA:mode})?.*\*.*',
    '^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"},\$GNGST,(?:%{NUMBER:gst_time:float})?,(?:%{NUMBER:rms:float})?,(?:%{NUMBER:semi_major:float})?,(?:%{NUMBER:semi_minor:float})?,(?:%{NUMBER:orientation:float})?,(?:%{NUMBER:lat_err:float})?,(?:%{NUMBER:lon_err:float})?,(?:%{NUMBER:alt_err:float})?.*\*.*',
    
    # Ignoring these messages entirely
    '^%{TIMESTAMP_ISO8601:timestamp:ts-"2006-01-02T15:04:05.000000Z"},\$(?:GPGSV|GLGSV|GNGSA|GNGRS).*?(\*.*)?'
      ]

[[processors.converter]]
  namepass = ["seapath_1"]
  [processors.converter.fields]
    # This converts the strings "08" or "09" into proper integer 8 or 9
    integer = ["zda_day", "zda_month", "num_satellites_1", "fix_quality_1", "zda_year"]

[[processors.starlark]]
  namepass = ["seapath_1"]
  source = '''
def apply(metric):
    # Latitude Conversion for INGGA (latitude_1)
    lat_raw = metric.fields.get('latitude_1')
    if lat_raw:
        deg = int(lat_raw / 100)
        min = lat_raw - (deg * 100)
        lat_deg = deg + (min / 60.0)
        if metric.fields.get('n_or_s_1') == "S": lat_deg = -lat_deg
        metric.fields['lat_deg'] = lat_deg

    # Longitude Conversion for INGGA (longitude_1)
    lon_raw = metric.fields.get('longitude_1')
    if lon_raw:
        deg = int(lon_raw / 100)
        min = lon_raw - (deg * 100)
        lon_deg = deg + (min / 60.0)
        if metric.fields.get('e_or_w_1') == "W": lon_deg = -lon_deg
        metric.fields['lon_deg'] = lon_deg

    return metric
'''

def raw_data_to_numeric(raw_data):
    if raw_data.startswith('$'):
        data = raw_data[1:]
        data = data.replace(',', '')
    else:
        data = raw_data.replace(' ', '')
        data = data.replace(',', '.')
    return float(data)

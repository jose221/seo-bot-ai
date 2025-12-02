import pandas as pd
import numpy as np


class SafeDict(dict):
    def __missing__(self, key):
        return None


def convertTypesOfJson(val):
    if isinstance(val, np.int64):
        return int(val)
    elif isinstance(val, pd.Timestamp):
        return val.isoformat()  # Convertimos pd.Timestamp a una cadena compatible con JSON
    elif isinstance(val, pd.DataFrame):
        return convertToJson(val)  # Este llamará a la representación JSON del DataFrame
    elif isinstance(val, dict):
        return {k: convertTypesOfJson(v) for k, v in
                val.items()}  # Hacemos una llamada recursiva por si el diccionario contiene np.int64 o Timestamp
    elif isinstance(val, list):
        return [convertTypesOfJson(v) for v in val]  # Por si la lista contiene np.int64 o Timestamp
    else:
        return val


def convertToJson(df):
    if isinstance(df, pd.DataFrame):
        # Si hay columnas categóricas, aseguramos añadir "NaN" como categoría válida
        for col in df.select_dtypes(['category']).columns:
            if "NaN" not in df[col].cat.categories:
                df[col] = df[col].cat.add_categories("NaN")

        # Convertimos los tipos de datos personalizados
        df = df.applymap(convertTypesOfJson)

        # Transformamos los valores infinitos
        df = df.applymap(lambda x: "inf" if isinstance(x, float) and np.isinf(x) else x)

        # Remplazamos valores NaN por "NaN"
        df = df.fillna("NaN")

        # Convertimos el DataFrame a formato dict JSON
        data = df.to_dict(orient='records')
    else:
        # Si no es un DataFrame, convertimos directamente
        data = convertTypesOfJson(df)
    return data



def responseJson(df, extra={}, code: int = 200) -> dict:
    safe_extra = SafeDict(extra) if extra is not None else {}

    data = convertToJson(df)

    response = {
        "code": code,
        "message": "Success",
        "length": len(data) if data is not None else 0,
        "data": data,
        "extra": convertToJson(safe_extra)
    }
    return response


def serialize_response_data(data):
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient='records')
    if isinstance(data, np.ndarray):
        data = data.tolist()
    if isinstance(data, dict):
        return {k: serialize_response_data(v) for k, v in data.items()}
    if isinstance(data, list):
        return [serialize_response_data(item) for item in data]
    if isinstance(data, pd.Timestamp):
        return data.isoformat()
    return data


import requests
from pathlib import Path
import sys
import yaml
import logging

logger = logging.getLogger(__name__)

# Add src to path to import database modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent / 'src'))

def download_data(url: str, table_name: str) -> str:
    """Get data from the provided URL and save it into raw data folder"""
    try:
        raw_data = requests.get(url, verify=False, timeout=30)

        if raw_data.status_code != 200:
            raise Exception(f"Failed to download data from {url}, status code: {raw_data.status_code}")

        file_name = f"{table_name}.json" if not table_name.endswith('.json') else table_name
        raw_dir = Path(__file__).parent.parent.parent / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        file_path = raw_dir / file_name

        with open(file_path, "w", encoding='utf-8') as f:
            f.write(raw_data.text)

        return f"Successfully downloaded {table_name}"

    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error downloading data from {url}: {str(e)}")
    except Exception as e:
        raise Exception(f"Error downloading data from {url}: {str(e)}")


def download_all_datasets() -> str:
    """Download all datasets from the API configuration file"""
    try:
        config_path = Path(__file__).parent.parent.parent / "data" / "config" / "data_apis.yaml"
        logger.info(f"Downloading all datasets from {config_path}")

        if not config_path.exists():
            return f"Configuration file not found at: {config_path}"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        results = []

        for dataset_name, dataset_info in config.items():
            try:
                url = dataset_info['url']
                if 'formato=json' not in url:
                    url = url + '?formato=json'
                table_name = dataset_info['table_name']
                logger.info(f"Downloading dataset {dataset_name} from {url} to {table_name}")
                result = download_data(url, table_name)
                results.append(f"{dataset_name}: {result}")
                logger.info(f"Dataset {dataset_name} downloaded successfully")
            except Exception as e:
                results.append(f"{dataset_name}: Error - {str(e)}")
                continue
        logger.info(f"All datasets downloaded successfully")
        return "\n".join(results)
    except Exception as e:
        logger.error(f"Error downloading datasets: {str(e)}")
        return f"Error downloading datasets: {str(e)}"

def download_all_datasets_tool() -> str:
    """Download all datasets from the API configuration file"""
    return download_all_datasets()

def is_ibge_format(data) -> bool:
    """Check if data is in IBGE API format"""
    if not isinstance(data, list) or len(data) == 0:
        return False

    first_item = data[0]
    if not isinstance(first_item, dict):
        return False

    ibge_keys = {'D1N', 'D2N', 'D3N', 'D4N', 'V'}
    return any(key in first_item for key in ibge_keys)

def transform_json_for_db(data, table_name: str) -> list:
    """Transform JSON data to format suitable for database insertion"""
    try:
        if not isinstance(data, list):
            return []

        if len(data) == 0:
            return []

        if is_ibge_format(data):
            import re

            header_row = data[0]
            data_rows = data[1:]

            column_mapping = {}
            for key, value in header_row.items():
                if isinstance(value, str):
                    cleaned = value.lower()
                    cleaned = re.sub(r'\(código\)', '_codigo', cleaned)
                    cleaned = re.sub(r'\(', '_', cleaned)
                    cleaned = re.sub(r'\)', '', cleaned)
                    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', cleaned)
                    cleaned = re.sub(r'_+', '_', cleaned)
                    cleaned = cleaned.strip('_')
                    if len(cleaned) > 63:
                        cleaned = cleaned[:60] + '_tr'
                    column_mapping[key] = cleaned or 'campo'
                else:
                    column_mapping[key] = key.lower()

            transformed = []
            for item in data_rows:
                row = {}
                for key, value in item.items():
                    clean_key = column_mapping.get(key, key.lower())

                    if value == '...':
                        row[clean_key] = None
                    elif value == '-':
                        row[clean_key] = None
                    else:
                        try:
                            if isinstance(value, str) and ',' in value and value.replace(',', '').replace('.', '').replace('-', '').isdigit():
                                row[clean_key] = float(value.replace(',', '.'))
                            elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                                row[clean_key] = float(value)
                            else:
                                row[clean_key] = value
                        except:
                            row[clean_key] = value

                transformed.append(row)

            return transformed
        else:
            return data

    except Exception as e:
        raise Exception(f"Error transforming data for {table_name}: {str(e)}")
import weaviate
from weaviate.classes.query import Filter
import logging
from pathlib import Path

outputs_folder = Path(__file__).parent.parent / "outputs"

logger = logging.getLogger(__name__)

client = weaviate.connect_to_custom(http_host="localhost", http_port=8080, http_secure=False, grpc_host="localhost", grpc_port=50051, grpc_secure=False)

def get_objects_count(collection_name: str) -> int:
    """Get the total number of objects given a collection"""

    collection = client.collections.use(collection_name)

    return collection.aggregate.over_all(total_count=True).total_count

if __name__ == "__main__":
    print(get_objects_count("PDFDocument"))
    client.close()
import os
import urllib.request
from pathlib import Path
from setuptools import find_packages
from setuptools import setup


def download_index():
    """Download FAISS search index from GCS."""
    models_dir = Path(__file__).parent / "models"
    index_path = models_dir / "index.faiss"
    url = "https://storage.googleapis.com/floportop-models/index.faiss"

    if index_path.exists():
        print(f"Index already exists: {index_path}")
        return

    models_dir.mkdir(exist_ok=True)
    print(f"Downloading index from {url}...")
    urllib.request.urlretrieve(url, index_path)
    print(f"Downloaded to {index_path}")

def read_requirements(path: str) -> list[str]:
    if not os.path.isfile(path):
        return []
    with open(path) as f:
        content = f.readlines()
    return [
        line.strip()
        for line in content
        if line.strip() and not line.startswith("#") and "git+" not in line
    ]


requirements = (
    read_requirements("requirements/prod.lock")
    or read_requirements("requirements.txt")
)


setup(name='floportop',
      version="0.0.1",
      description="Movie prediction engine",
      packages=find_packages(where="src"),
      package_dir={"": "src"},
      install_requires=requirements,
      # include_package_data: to install data from MANIFEST.in
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'download-index=setup:download_index',
          ],
      },
      zip_safe=False)

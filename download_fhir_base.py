#!/usr/bin/env python3
"""
Download FHIR R4 Base Resources
Downloads the official FHIR R4 specification resources to fix validation warnings.
"""

import urllib.request
import zipfile
import json
import os
from pathlib import Path


def download_fhir_r4_resources():
    """Download and extract FHIR R4 specification resources."""
    print("🔽 Downloading FHIR R4 specification resources...")
    
    # Official FHIR R4 definitions download URL
    url = "http://hl7.org/fhir/R4/definitions.json.zip"
    zip_file = "definitions.json.zip"
    extract_dir = "fhir_base_resources"
    
    try:
        # Download the zip file
        print(f"📥 Downloading from: {url}")
        urllib.request.urlretrieve(url, zip_file)
        print(f"✅ Downloaded: {zip_file}")
        
        # Create extraction directory
        Path(extract_dir).mkdir(exist_ok=True)
        
        # Extract the zip file
        print(f"📂 Extracting to: {extract_dir}/")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Clean up zip file
        os.remove(zip_file)
        print(f"🗑️ Cleaned up: {zip_file}")
        
        # Count extracted files
        json_files = list(Path(extract_dir).glob("*.json"))
        print(f"📊 Extracted {len(json_files)} FHIR resource files")
        
        # Find the specific ValueSets we need
        needed_valuesets = [
            "marital-status",
            "relatedperson-relationshiptype"
        ]
        
        found_valuesets = []
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    resource = json.load(f)
                    
                if resource.get('resourceType') == 'ValueSet':
                    resource_id = resource.get('id', '')
                    if resource_id in needed_valuesets:
                        found_valuesets.append(resource_id)
                        print(f"✅ Found needed ValueSet: {resource_id}")
                        
            except Exception as e:
                continue
        
        print(f"\n🎯 Summary:")
        print(f"  Total FHIR resources downloaded: {len(json_files)}")
        print(f"  Needed ValueSets found: {len(found_valuesets)}/{len(needed_valuesets)}")
        
        if len(found_valuesets) == len(needed_valuesets):
            print("✅ All required ValueSets are now available!")
        else:
            missing = set(needed_valuesets) - set(found_valuesets)
            print(f"⚠️ Still missing: {', '.join(missing)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading FHIR resources: {e}")
        return False


def main():
    """Main function to download FHIR resources."""
    print("🚀 FHIR R4 Base Resources Downloader")
    print("=" * 50)
    
    success = download_fhir_r4_resources()
    
    if success:
        print("\n🎉 Download completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update the resource loader to include fhir_base_resources/")
        print("2. Restart your validation server")
        print("3. Test validation again - warnings should be resolved!")
    else:
        print("\n❌ Download failed. Please check your internet connection and try again.")


if __name__ == "__main__":
    main()

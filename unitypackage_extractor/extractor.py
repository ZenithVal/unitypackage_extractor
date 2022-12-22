import tarsafe
import tempfile
import sys
import os
import time
import shutil
import re
from pathlib import Path

def extractPackage(packagePath, outputPath=None, encoding='utf-8', with_meta=False):
  """
  Extracts a .unitypackage into the current directory
  @param {string} packagePath The path to the .unitypackage
  @param {string} [outputPath=os.getcwd()] Optional output path, otherwise will use cwd
  """
  if not outputPath:
    outputPath = os.getcwd() # If not explicitly set, WindowsPath("") has no parents, and causes the escape test to fail

  with tempfile.TemporaryDirectory() as tmpDir:
    # Unpack the whole thing in one go (faster than traversing the tar)
    with tarsafe.open(name=packagePath, encoding=encoding) as upkg:
      upkg.extractall(tmpDir)

    # Extract each file in tmpDir to final destination
    for dirEntry in os.scandir(tmpDir):
      assetEntryDir = f"{tmpDir}/{dirEntry.name}"
      has_meta = False
      is_dir = False
      if not os.path.exists(f"{assetEntryDir}/pathname"):
        continue #Doesn't have the required files to extract it
      if not os.path.exists(f"{assetEntryDir}/asset"):
          is_dir = True
      if with_meta:
          meta_path = f"{assetEntryDir}/asset.meta"
          if os.path.exists(meta_path):
              has_meta = True

      # Has the required info to extract
      # Get the path to output to from /pathname
      with open(f"{assetEntryDir}/pathname", encoding=encoding) as f:
        pathname = f.readline()
        pathname = pathname[:-1] if pathname[-1] == '\n' else pathname #Remove newline
        # Replace windows reserved chars with '_' that arent '/'
        if os.name == 'nt':
          pathname = re.sub(r'[\>\:\"\|\?\*]', '_', pathname)

      # Figure out final path, make sure that it's inside the write directory
      assetOutPath = os.path.join(outputPath, pathname)
      if Path(outputPath).resolve() not in Path(assetOutPath).resolve().parents:
        print(f"WARNING: Skipping '{dirEntry.name}' as '{assetOutPath}' is outside of '{outputPath}'.")
        continue

      #Extract to the pathname
      if not is_dir:
          print(f"Extracting '{dirEntry.name}' as '{pathname}'")
          os.makedirs(os.path.dirname(assetOutPath), exist_ok=True) #Make the dirs up to the given folder
          shutil.move(f"{assetEntryDir}/asset", assetOutPath)

      if with_meta and has_meta:
          print(f"Extracting '{dirEntry.name}' .meta as '{pathname}.meta'")
          metaOutPath = os.path.join(outputPath, pathname+'.meta')
          os.makedirs(os.path.dirname(assetOutPath), exist_ok=True) #Make the dirs up to the given folder
          shutil.move(f"{assetEntryDir}/asset.meta", metaOutPath)

def cli(args):
  """
  CLI entrypoint, takes CLI arguments array
  """
  if not args:
    raise TypeError("No .unitypackage path was given. \n\nUSAGE: unitypackage_extractor [XXX.unitypackage] (optional/output/path)")
  startTime = time.time()
  with_meta = True if "--with-meta" in args else False
  if with_meta:
      print("extract .meta files")
  extractPackage(args[0], args[1] if len(args) > 1 else "", with_meta=with_meta)
  print("--- Finished in %s seconds ---" % (time.time() - startTime))

if __name__ == "__main__":
  cli(sys.argv[1:])

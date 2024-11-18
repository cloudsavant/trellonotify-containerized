# Set variables
$BUCKET_NAME = "trellonotify-source-bucket"
$SOURCE_DIR = ".\app"
$ZIP_NAME = "code.zip"
$BUILD_DIR = ".\build"
$CURRENT_DIR = Get-Location

# Create a temporary directory for deployment
if (-not (Test-Path $BUILD_DIR)) {
    New-Item -Path $BUILD_DIR -ItemType Directory
}

# Zip the source code
Write-Host "Zipping source code..."
Set-Location $SOURCE_DIR
Compress-Archive -Force -Path * -DestinationPath "$CURRENT_DIR\$BUILD_DIR\$ZIP_NAME"

# Return to the original directory
Set-Location $CURRENT_DIR

# Upload the zipped file to GCS
Write-Host "Uploading to GCS..."
gsutil cp "$BUILD_DIR\$ZIP_NAME" "gs://$BUCKET_NAME/"

Write-Host "Build done!"

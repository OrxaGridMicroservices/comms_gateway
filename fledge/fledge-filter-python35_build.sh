# Clone the repository
git clone https://github.com/fledge-iot/fledge-filter-python35.git
cd fledge-filter-python35

# Install pkg-config (this should resolve the CMake error)
sudo apt-get update
sudo apt-get install -y pkg-config

# Create the build directory
mkdir -p build
cd build

# Run CMake
cmake -DCMAKE_BUILD_TYPE=Release -DFLEDGE_INCLUDE=/usr/local/fledge/include/ -DFLEDGE_LIB=/usr/local/fledge/lib/ ..

# Build the project
make

# Check if the libpython35.so file exists before attempting to copy
if [ -f "libpython35.so" ]; then
    # If the directory does not exist, create it
    if [ ! -d "${FLEDGE_ROOT}/plugins/filter/python35" ]; then
        sudo mkdir -p $FLEDGE_ROOT/plugins/filter/python35
    fi

    # Copy the libpython35.so file to the target directory
    sudo cp libpython35.so $FLEDGE_ROOT/plugins/filter/python35
else
    echo "Error: libpython35.so file not found!"
    exit 1
fi

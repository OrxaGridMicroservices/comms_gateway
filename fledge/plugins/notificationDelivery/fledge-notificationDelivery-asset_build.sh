FLEDGENOTIFVERSION=2.6.0
RELEASE=2.6.0
OPERATINGSYSTEM=ubuntu2004
ARCHITECTURE=x86_64
FLEDGELINK="http://archives.fledge-iot.org/$RELEASE/$OPERATINGSYSTEM/$ARCHITECTURE"

wget --no-check-certificate ${FLEDGELINK}/fledge-notify-asset_${FLEDGENOTIFVERSION}_${ARCHITECTURE}.deb
dpkg --unpack ./fledge-notify-asset_${FLEDGENOTIFVERSION}_${ARCHITECTURE}.deb
apt-get install -yf
apt-get clean -y
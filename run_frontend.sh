#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/frontend"

echo "==================================================================="
echo " Starting Vanguard ClaimOS Next.js Frontend Portal (Port 3000)"
echo "==================================================================="

npm run dev

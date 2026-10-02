@echo off
REM ====================================================================
REM  build-and-push-af10.bat
REM  Build the psybot-api Docker image and publish it to Docker Hub
REM  under the user "af10".
REM
REM  Usage (from a Windows shell, in the repo root):
REM     build-and-push-af10.bat
REM     build-and-push-af10.bat 1.2.3          REM explicit version tag
REM
REM  Requirements:
REM     - Docker Desktop installed and running
REM     - `docker login` already executed at least once (this script
REM       re-authenticates if needed)
REM
REM  What it does:
REM     1. Reads VERSION (default: git short SHA, or first arg)
REM     2. Builds the multi-stage image from ./Dockerfile
REM     3. Tags it af10/psybot-api:<VERSION> and af10/psybot-api:latest
REM     4. Pushes both tags to Docker Hub
REM     5. Prints the image digest + size on success
REM ====================================================================

setlocal EnableDelayedExpansion

REM ---- 1. Resolve version tag ------------------------------------------
if not "%~1"=="" (
    set "VERSION=%~1"
) else (
    REM Try git short SHA; fall back to "dev" if git is unavailable.
    for /f "delims=" %%v in ('git rev-parse --short HEAD 2^>nul') do (
        set "VERSION=%%v"
    )
    if "!VERSION!"=="" set "VERSION=dev"
)

set "IMAGE=af10/psybot-api"
set "DOCKERHUB_USER=af10"

echo.
echo ============================================================
echo  psybot-api -> %IMAGE%:%VERSION%
echo  Docker Hub user: %DOCKERHUB_USER%
echo ============================================================
echo.

REM ---- 2. Make sure we're logged in to Docker Hub ---------------------
echo [1/4] Checking Docker Hub credentials...
docker info 2>nul | findstr /C:"Username: %DOCKERHUB_USER%" >nul
if errorlevel 1 (
    echo     Not logged in as %DOCKERHUB_USER%. Running 'docker login'...
    docker login -u %DOCKERHUB_USER%
    if errorlevel 1 (
        echo.
        echo *** docker login failed. Aborting. ***
        exit /b 1
    )
) else (
    echo     Already authenticated as %DOCKERHUB_USER%.
)
echo.

REM ---- 3. Build the image --------------------------------------------
echo [2/4] Building image (this can take 2-5 minutes on a cold cache)...
echo.

docker build ^
    --tag %IMAGE%:%VERSION% ^
    --tag %IMAGE%:latest ^
    --label "org.opencontainers.image.source=https://github.com/f80dev/bobot" ^
    --label "org.opencontainers.image.version=%VERSION%" ^
    --label "org.opencontainers.image.created=%DATE% %TIME%" ^
    .

if errorlevel 1 (
    echo.
    echo *** docker build failed. Aborting. ***
    exit /b 1
)
echo.

REM ---- 4. Push the tags ----------------------------------------------
echo [3/4] Pushing %IMAGE%:%VERSION% ...
docker push %IMAGE%:%VERSION%
if errorlevel 1 (
    echo *** Push of :%VERSION% failed. Aborting. ***
    exit /b 1
)

echo.
echo [4/4] Pushing %IMAGE%:latest ...
docker push %IMAGE%:latest
if errorlevel 1 (
    echo *** Push of :latest failed. Aborting. ***
    exit /b 1
)

REM ---- 5. Report -----------------------------------------------------
echo.
echo ============================================================
echo  Done.
echo.
echo  Image:    %IMAGE%:%VERSION%
docker images %IMAGE%:%VERSION% --format "  Size:     {{.Size}}" 2>nul
echo  Pull:     docker pull %IMAGE%:%VERSION%
echo  Run:      docker run --rm -p 8080:8080 ^
echo                   -e DEEPSEEK_API_KEY=sk-... ^
echo                   -e DEEPSEEK_MOCK=0 ^
echo                   %IMAGE%:%VERSION%
echo ============================================================
echo.

endlocal
exit /b 0
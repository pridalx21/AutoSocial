@echo off
set /p OPENAI_API_KEY="Enter your OpenAI API key: "
setx OPENAI_API_KEY "%OPENAI_API_KEY%"
echo API key has been set!
pause

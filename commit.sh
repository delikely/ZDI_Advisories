git diff --exit-code
if [ "$?" !=  "0"];then
    git config --global user.email delikely@gmail.com
    git config --global user.name delikely
    git add advisories
    git commit -m "update(`date +'%Y-%m-%d'`)"
fi
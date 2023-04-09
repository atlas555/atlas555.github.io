git add .
msg="updating site on $(date)" 
git commit -m "$msg"
git pull -r
git push origin source

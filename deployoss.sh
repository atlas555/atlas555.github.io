echo "start hugo build"
hugo --minify -D --gc --debug

echo "---------- end hugo build -------------\n"

echo "start push github"

sh ./push.sh

echo "--------- end git push -------------\n"

echo "start copy public to oss"
ossutil cp -ru ./public oss://hugo-site/

echo "-------- end oss copy ------------\n"

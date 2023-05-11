echo "start hugo build"
hugo --minify -D --gc --debug

echo "start copy public to oss"
ossutil cp -ru ./public oss://hugo-site/

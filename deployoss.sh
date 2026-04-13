set -e

echo "start hugo build"
# hugo --minify -D --gc --debug  # remove --buildDrafts    # or -D
hugo --minify --gc --logLevel info

echo "---------- end hugo build -------------\n"

echo "start push github"

sh ./push.sh

echo "--------- end git push -------------\n"

echo "start sync public to oss"
ossutil sync ./public oss://hugo-site/ --checkers 64 --delete --size-only -f

echo "-------- end oss copy ------------\n"

#!/usr/bin/env bash
git branch -m dev master # Rename branch locally
git push origin :dev # Delete the old branch
git push --set-upstream origin master # Push the new branch, set local branch to track the new remote
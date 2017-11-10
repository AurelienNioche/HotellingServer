#!/usr/bin/env bash
git branch -m new_dev dev # Rename branch locally
git push origin :new_dev # Delete the old branch
git push --set-upstream origin dev # Push the new branch, set local branch to track the new remote

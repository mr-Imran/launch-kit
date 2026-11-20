# Launch checklist for envdiff

In the order to do them. Commands run from the repository root. Nothing here
has been done for you: no commit, no push, nothing set on GitHub.

`launch/` is in `.gitignore`, so this file and the drafts stay on your machine.

## A. Decisions only you can make

- [ ] **1. Choose a license.** Without a LICENSE file nobody may legally use
  the code, and it is the first thing a Hacker News reader checks. Once you
  have chosen:

  - Add the license text as `LICENSE` in the repository root. GitHub has the
    texts ready: on the repository page, **Add file > Create new file**, type
    `LICENSE` as the name, then **Choose a license template**. Or copy the
    text from choosealicense.com.
  - Add this at the end of `README.md`, with the real name:

    ```markdown
    ## License

    <name of the license>. See [LICENSE](LICENSE).
    ```

  - Optional, for the package metadata: add `license = {text = "<name>"}`
    under `[project]` in `pyproject.toml`. (Checked: this form builds with
    the current setuptools release, and it is the form `setuptools>=61`
    understands.)

- [ ] **2. Replace `OWNER` with your GitHub handle.** It appears in
  `README.md` (2 places), `pyproject.toml` (2) and the files in `launch/`.
  One command, with your handle in place of `your-handle`:

  ```sh
  grep -rl OWNER README.md pyproject.toml launch/ | xargs sed -i 's/OWNER/your-handle/g'
  ```

  Then check that nothing is left. This should print nothing:

  ```sh
  grep -rn OWNER README.md pyproject.toml CONTRIBUTING.md launch/
  ```

  If the GitHub repository will not be called `envdiff`, change the URLs in
  the same files too.

- [ ] **3. Decide about the traceback on a missing file.**
  `python3 envdiff.py examples/dev.env nope.env` ends in a Python traceback
  and exit status 1, the same status as "the files differ". It is the first
  thing someone trying the tool will hit. A tested fix is in
  `launch/handle-unreadable-files.patch`. It prints
  `envdiff: [Errno 2] No such file or directory: 'nope.env'`, exits with
  status 2, and adds one test:

  ```sh
  git apply launch/handle-unreadable-files.patch
  python3 -m pytest
  ```

  If you apply it: in `README.md`, delete the first bullet under
  "Limitations" and change the exit status table row for 2 to "Wrong
  arguments, or a file that cannot be read". Delete the traceback sentence
  from the two Reddit drafts. If you do not apply it, the README and the
  drafts already describe the current behaviour.

- [ ] **4. Check the name on PyPI.** The README says "not on PyPI yet". I did
  not look the name up, because that tells a public service the name of a
  project you have not announced. When you are ready:

  ```sh
  pip index versions envdiff
  ```

  If that lists versions, another project already has the name. People who
  type `pip install envdiff` out of habit would get that one, so say it next
  to the install command in the README, and plan a different distribution
  name for your own release.

## B. Push it privately and look at it

- [ ] **5. Commit.**

  ```sh
  git add -A
  git commit -m "Prepare for launch: README, demo, package metadata, CONTRIBUTING"
  ```

- [ ] **6. Create the repository as private and push.** This lets you see the
  page before anyone else does.

  ```sh
  gh repo create envdiff --private --source=. --remote=origin --push
  ```

- [ ] **7. Set the description and topics.**

  ```sh
  gh repo edit OWNER/envdiff --description "Compare two .env files and see which keys are missing or different, without printing the values"
  gh repo edit OWNER/envdiff --add-topic cli --add-topic command-line-tool --add-topic python --add-topic dotenv --add-topic env --add-topic environment-variables --add-topic diff --add-topic configuration --add-topic devops
  ```

  Repositories using each topic on 2026-11-20: python 1,048,722; cli 167,324;
  devops 52,710; command-line-tool 10,101; configuration 8,866; dotenv 6,811;
  diff 3,465; environment-variables 3,355; env 2,532. Leave the homepage
  empty: there is no docs site or package page yet.

- [ ] **8. Upload the social preview.** There is no API for this. Repository
  page > **Settings** > **General** > **Social preview** > **Edit** >
  **Upload an image** > pick `assets/social-preview.png`.

- [ ] **9. Look at the page.** The demo plays under the pitch, the code blocks
  and the table render, the CONTRIBUTING link works. Check it in both the
  light and the dark GitHub theme.

## C. Go public

- [ ] **10. Make it public.** Repository page > **Settings** > **General** >
  **Danger Zone** > **Change visibility**. Check that Issues are enabled
  (Settings > General > Features).

- [ ] **11. Test the install on a clean environment**, right after it is
  public and before you post anywhere:

  ```sh
  python3 -m venv /tmp/envdiff-check
  /tmp/envdiff-check/bin/pip install git+https://github.com/OWNER/envdiff
  /tmp/envdiff-check/bin/envdiff examples/dev.env examples/prod.env
  ```

  Also run the `pipx install` line from the README if you have pipx. I could
  not: pipx is not installed here, so I verified the same install with pip
  from a local git URL instead. `pyproject.toml` says Python 3.8+. I ran
  everything on 3.14 only and checked that the source parses as 3.8 syntax.
  If you have an older Python around, run the tests on it once.

- [ ] **12. Tag the first release.**

  ```sh
  git tag v0.1.0 && git push origin v0.1.0
  gh release create v0.1.0 --title "v0.1.0" --notes "First public release."
  ```

## D. Post

- [ ] **13. Write the Show HN text yourself**, from `launch/show-hn.md`.
  Hacker News asks for no generated text, so there is no draft. Read section
  2 of that file first: it may be better to post on Reddit first.
- [ ] **14. Rewrite the Reddit drafts in your own words** and fill the gaps
  marked `[[author: ...]]` (`launch/reddit.md`).
- [ ] **15. Read the rules of each subreddit** before posting there, including
  any rule on AI-written posts and on self-promotion.
- [ ] **16. Spread the posts over several days.** For each one, block a few
  hours afterwards to answer comments.
- [ ] **17. After posting:** reply to every question in your own words, fix
  what people report, thank the people who criticise. Never ask for upvotes
  or stars.

## E. Later, when you publish to PyPI

- PyPI does not resolve relative image paths, so `assets/demo.svg` will show
  as a broken image on the package page. Before uploading, point the image in
  `README.md` at an absolute URL of the file on GitHub, and look at the page
  on TestPyPI first.
- Then change the install command in the README and remove "not on PyPI yet".

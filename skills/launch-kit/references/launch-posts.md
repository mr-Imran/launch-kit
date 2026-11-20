# Launch posts

A launch post is the author telling a community "I made this, here is what it
does, tell me what you think." The posts that do well read like that. The ones
that sink read like advertising.

Prepare one file per channel in `launch/`. The author writes or rewrites the
final words and posts them personally.

**Hacker News is different from the others: do not write its post.** Its
guidelines ask for text the author wrote themselves, so for Show HN you
prepare notes, not a draft. Section 3 explains.

## Contents

1. Principles
2. What you can write and what only the author can
3. Show HN: notes, not a draft
4. Reddit
5. X
6. Other channels
7. Timing
8. Files to write
9. Launch-day checklist

## 1. Principles

- **First person, plain words.** "I built this because..." beats any headline.
  Developer communities punish marketing language quickly and publicly.
- **Lead with the problem**, then what the tool does about it, then how it
  works. People upvote things they can picture using.
- **Name the limits.** Say what does not work yet, including what you found by
  running the tool yourself (see step 1 of the workflow). The limits a README
  lists are rarely the ones a commenter hits first. If you found a bug, put it
  in the post as a known limit and tell the author it would be better fixed
  before posting.
- **Only true claims.** No invented numbers, users or comparisons. If the
  project is a day old, it is fine for it to look a day old.
- **Never ask for votes or stars**, and never suggest that friends upvote.
  Hacker News and Reddit both treat this as manipulation and bury or remove
  the post. Do not draft messages that ask for it.
- **One account, the author's own.** No second accounts, no posting on the
  author's behalf.
- **Each community gets its own post.** The same text pasted into five places
  is recognised and treated as spam.
- **Respect each community's stance on generated text.** Hacker News asks for
  none at all (section 3). Many subreddits have their own rule about
  AI-written posts. A draft from you is a starting point for the author to
  rewrite in their own words, and every draft file says so at the top.
- **Every command in a post must work on the day.** In a post, use the
  command the README gives its readers, since that is what the author intends
  to publish, and put "verify this command" at the top of the file when you
  could not check it. Do not swap in a clone-and-run command the author never
  advertised.

## 2. What you can write and what only the author can

Most of a post comes from the repository: what the tool does, how it works,
its real output, its limits. Write all of that.

If the README already explains why the project exists, turn that into first
person and use it. It is the author's own account; mark it for them to check.

Some things are not in the repository: the author's name and background, the
moment that made them build it, the feedback they want, how it compares with
tools they tried. Do not make these up. Leave a marked gap:

```
[[author: one or two sentences on why you built this]]
```

Use a gap only where the text truly needs something you cannot know, and
list the gaps at the top of the draft. A draft that is half gaps has not
saved the author any work.

Use the README's sample output, or output from the repository's own example
data. Output from your own run can carry the local user name, paths and
process names into a public post.

Readers will ask how the project compares with tools the repository never
mentions. You may list the obvious ones under "questions to expect", marked
as your outside knowledge and not checked. Do not write the comparison: you
have not used them side by side, and the author may have.

## 3. Show HN: notes, not a draft

Hacker News has a section for things people have made. Two of its rules decide
what you may prepare.

From `news.ycombinator.com/newsguidelines.html`:

> Please don't put generated text in HN posts. Write your text
> yourself—HN is for sharing between humans.

The same page says of comments: "Don't post generated text or AI-edited text."

So **do not write the Show HN text, and do not offer to polish what the author
writes.** A generated post breaks the rules of the place it is posted in, and
readers there are quick to spot one. What helps the author is everything
around the writing: the rules, the facts, and an outline they can fill in ten
minutes. Tell them why, in one or two sentences, so the notes do not look like
a half-finished job.

If the author hears this and still asks for a full draft, it is their account
and their decision. Write it, and repeat the guideline at the top of the file.

From `news.ycombinator.com/showhn.html`:

- "Show HN is for something you've made that other people can play with."
  A repository with working install instructions qualifies. Blog posts,
  sign-up pages, newsletters, landing pages and fundraisers do not.
- "The project should be non-trivial. Don't post quickly-generated one-offs;
  anybody can do that now." Be honest with the author about this. If the
  project is very small or very new, say that Show HN may be a hard room for
  it and that a specific subreddit could be a better first stop. The decision
  is theirs.
- "If your work isn't ready for users to try out, please don't do a Show HN."
- "Please don't ask friends to upvote or comment."
- New versions of something already shown ("Foo 1.3.1 is out") are generally
  not substantive enough.

Write `launch/show-hn.md` as notes with these parts:

1. **Read this first.** The generated-text guideline, quoted, and a line
   saying that everything below is material to write from, not text to paste.
   This is the file's "Before you post" block (section 8); put the commands
   and links to verify here too, rather than writing a second block.
2. **Does it qualify?** Can people try it today, and with which command? Is it
   non-trivial? Your honest reading, in a sentence or two.
3. **Title format.** `Show HN: Name – what it does`. The submission form
   limits titles to 80 characters. The guidelines ask for no uppercase for
   emphasis, no exclamation points, and no saying how great it is. Give the
   format and the facts a title should carry (the name, the verb, the object);
   the author words it.
4. **URL.** The repository link, and whether it came from a git remote or
   needs checking.
5. **Facts to draw on**, as short notes rather than sentences: what it does,
   how it works (this audience reads the code, so the mechanism and the
   trade-offs matter most), what you verified by running it, what does not
   work yet, what similar tools exist if the repository names any.
6. **An outline for the first comment**, as questions the author answers in
   their own words: who are you, what made you build it, what does it do, how
   does it work, what is rough, what feedback do you want.
7. **Formatting.** Hacker News is plain text, not Markdown. Blank line between
   paragraphs. Code and terminal output are indented by two or more spaces
   with a blank line before and after; backticks and fenced blocks show up
   literally. No bullet syntax. `*text*` gives italics. URLs link themselves.
8. **On the day.** Be there to answer for a few hours; reply in your own
   words; do not ask anyone to upvote.

Keep the notes in fragments and third person ("single file, no dependencies",
"fails with a traceback on a missing path") so they cannot be mistaken for
post text.

## 4. Reddit

Every subreddit has its own rules on self-promotion: some forbid it, some
allow it on certain days or in a showcase thread, some require a flair.
**The author must read the rules of each subreddit before posting.** Say this
in the draft, and do not present any subreddit as safe to post in.

Suggest two or three subreddits where the tool's users already are, with the
reason for each: a language community (r/Python, r/rust, r/node), a domain
community (r/devops, r/selfhosted, r/commandline), or a showcase community
(r/SideProject, r/opensource). Smaller, more specific communities usually
respond better than large general ones.

**Title.** Say what it is. No clickbait, no "I spent 6 months...".

```
I made a small CLI that renames photos by the date they were taken
```

**Body.** The problem in a few sentences, what the tool does, one real
example with output, how it works in a line or two, what it does not do, the
link, and an invitation to say what is wrong or missing.

Write a separate version for each subreddit, adjusted to what that community
cares about (the language community wants to hear about the implementation,
the domain community about the workflow). When the author asked for "a Reddit
post", two versions are enough: the best fit and one alternative. Tell the
author to stay and answer comments, and not to post to all of them on the
same day.

**Formatting.** Reddit uses Markdown, but fenced code blocks do not render on
old Reddit and some apps. Indent code and output by four spaces instead. In
`reddit.md`, wrap each title and body in its own fenced `text` block so the
author can copy it exactly, indents included, and tell them to paste it with
the editor in Markdown mode.

**Generated text.** Many subreddits have a rule about AI-written posts, and
moderators remove what reads like one. Put this at the top of `reddit.md`:
the draft is a starting point, the author should check each subreddit's rule
on it and rewrite the post in their own words before posting.

## 5. X

A short thread: three to five posts, each within 280 characters.

1. The pitch, plus the demo as a GIF or MP4. X does not accept SVG, so if only
   an SVG demo exists, say so in the draft and point to Route B in `demo.md`.
2. The problem it solves, in one concrete example.
3. How it works, or the one design decision worth mentioning.
4. What is not there yet, and what is next.
5. The link.

No hashtag strings. No "🧵👇". Count the characters of every post and write
the count next to each one in the draft.

## 6. Other channels

Mention those that fit, with one line on why, and draft only if the author
wants them:

- **A write-up** (dev.to, Hashnode, a personal blog): the story of the problem
  and how the tool works. It keeps bringing visitors long after launch day.
- **Lobsters**: invitation-only, and its members dislike drive-by
  self-promotion. Only for authors who are already members.
- **Product Hunt**: better for products with a UI than for libraries.
- **Curated lists** (awesome-*): open a pull request following that list's
  contribution rules, usually after the project has some history.
- **Community showcases**: the Discord or forum of the language or framework,
  in the channel meant for it.
- **Newsletters** for the language or domain often accept submissions.

## 7. Timing

There is no reliable best hour, and advice about it is mostly anecdote. What
does matter: the author should post when they can stay for the next few hours,
because early questions answered quickly are what keep a thread alive. Spread
channels over several days so each one gets attention.

## 8. Files to write

Write a file for each channel the author asked for. A whole launch always
gets the checklist as well. When they asked for a whole launch and named no
channels, write all four:

```
launch/
  show-hn.md       notes for the author to write from (section 3), not a draft
  reddit.md        subreddits with reasons and rule reminders, a draft for each
  x-thread.md      numbered posts with character counts
  checklist.md     launch-day checklist with every manual step
```

When they asked for a whole launch and named channels ("I want to post on
Hacker News and Reddit"), write those channels plus the checklist. When they
asked only for specific posts and nothing else, write only those, and skip
the checklist.

Start each file with a short "Before you post" block: the community's stance
on generated text, the gaps to fill, the commands and links to verify (the
install command, the repository URL when it came from a manifest rather than
a git remote), and the rule reminders for that channel.

**Keeping drafts out of the release.** Drafts are working notes, not part of
the project. In a full launch preparation, add `launch/` to `.gitignore` and
say that you did. When the author asked you not to change existing files,
leave `.gitignore` alone and tell them instead. Either way, mention it if the
project publishes its whole folder (an npm package with no `files` list, for
example), because `launch/` would be published with it. The audit reads the
folder from disk, so ignored drafts still count.

## 9. Launch-day checklist

Adapt this into `launch/checklist.md` with the real commands and links, in the
order the author will do them:

- [ ] Decisions made: license chosen, `OWNER` replaced with the real handle.
- [ ] Changes committed. If the repository has never been pushed: create it
      private first and push (`gh repo create NAME --private --source=.
      --remote=origin --push`).
- [ ] Description and topics set (commands included).
- [ ] Social preview uploaded: Settings > General > Social preview.
- [ ] README and demo look right on the GitHub page; all links work.
- [ ] Install command tested on a clean machine or container.
- [ ] Repository made public (Settings > General > Danger Zone); issues
      enabled; first release tagged.
- [ ] Show HN text written by the author, from the notes, in their own words.
- [ ] Reddit and X drafts rewritten in the author's voice; gaps marked
      `[[author: ...]]` filled in.
- [ ] Subreddit rules read for each planned post, including any rule on
      AI-written posts.
- [ ] Time blocked to answer comments for a few hours after each post.
- [ ] After posting: reply to every question, fix what people report, and
      thank the people who criticise.

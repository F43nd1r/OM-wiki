### How to run this thing

#### You need:

* A python3 interpreter
* [PRAW](https://github.com/praw-dev/praw)

#### You have to:

* Compile a suitable "post to reddit" section, at the end of the file
* Replace all the mentions to `reddit_secret` with your token/password

The relevant part of `reddit_secret.py` is:

```python
client_id     = <client_id>
client_secret = <client_secret>
username      = <username>
password      = <password>
```

Consult the PRAW documentation for help filling these variables.

Running `./wiki_builder.py` will then:

* output at stdout the table part
* post to reddit (or somewhere else) the whole page.
* create/update `scores.csv`, the wiki storage
* create/update `timestamp.utc`, to avoid double-parsing

#### Maintainance:

Editing the `prefix`/`suffix` will change the other parts of the page.

It's possible to add scores directly to `scores.csv`, the frontier will be rebuilt next run.

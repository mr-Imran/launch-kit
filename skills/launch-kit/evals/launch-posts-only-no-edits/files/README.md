# portwho

See which process is holding a port, and kill it if you want.

```sh
npx portwho 3000
```

```
PORT   PID     COMMAND         USER
3000   48213   node            sam
```

## Why

`EADDRINUSE` again. `lsof -i :3000` works, but nobody remembers the flags, and
the output is different on macOS and Linux. portwho prints the same small table
on both, and can stop the process for you.

## Install

```sh
npm install -g portwho
```

Or run it once with `npx portwho <port>`. Needs Node 18 or newer.

## Usage

```sh
portwho 3000            # who is on 3000?
portwho 3000 8080       # several ports at once
portwho 3000 --kill     # send SIGTERM to whatever is there
portwho 3000 --json     # for scripts
```

## How it works

It calls `lsof` on macOS and `ss` on Linux and normalises the output. There are
no npm dependencies. Windows is not supported yet.

## License

MIT

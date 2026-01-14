# SimpleRunbook
This is a simple test runbook that demonstrates the basic functionality of the stage0_runner utility. It performs a simple echo operation and lists the current directory.

# Environment Requirements
```yaml
TEST_VAR: A test environment variable for demonstration purposes
```

# File System Requirements
```yaml
Input:
```

# Required Claims
```yaml
roles: sre, api
```
This section is optional. If present, the token must include the specified claims to execute or validate the runbook.
- `roles`: List of roles (comma-separated) that are allowed to execute/validate this runbook
- Other claims can be specified as key-value pairs where the value is a comma-separated list of allowed values

# Script
```sh
#! /bin/zsh
echo "Running SimpleRunbook"
echo "Test variable value: ${TEST_VAR:-not set}"
echo "Current directory: $(pwd)"
echo "Listing files:"
ls -la
echo "SimpleRunbook completed successfully"
```

# History

### 2026-01-14T21:32:18.051Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-8d02b6f3-utpf70qa
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 909 mikestorey  staff  29088 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:18.067Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: custom_test_value
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-e39ab381-3icakaxd
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 909 mikestorey  staff  29088 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:18.131Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_0
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-4f7406a8-uru7d5yk
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 913 mikestorey  staff  29216 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:18.131Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_0
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-36be685c-n75a6a3g
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 913 mikestorey  staff  29216 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:18.133Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_0
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-95f4aad8-j05vm5bc
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 913 mikestorey  staff  29216 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:18.134Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_0
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-a62ba5b6-yii0z5f7
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 911 mikestorey  staff  29152 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:18.135Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_0
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-1ff5d97a-t04_z_sp
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 910 mikestorey  staff  29120 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:18.230Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_0
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-7e4fb6f2-nq4efrlj
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 909 mikestorey  staff  29088 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:18.244Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_1
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-e6891abf-8pfglheg
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 909 mikestorey  staff  29088 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:18.258Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_2
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-945bad2b-_e2_d087
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 909 mikestorey  staff  29088 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:18.272Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_4
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-7c585fb4-o0q432ez
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 909 mikestorey  staff  29088 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.419Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-bab56111-umsjialp
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 914 mikestorey  staff  29248 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.438Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: custom_test_value
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-ed0816d2-nm0qalz5
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 914 mikestorey  staff  29248 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.502Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_4
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-d10149fc-8g9d2h_r
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 918 mikestorey  staff  29376 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.502Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_4
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-20b40c94-w5ex5b6_
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 918 mikestorey  staff  29376 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.504Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_4
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-4cf4a61a-1xffm0gr
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 918 mikestorey  staff  29376 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.504Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_4
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-c5b7b29b-9o5jcf2q
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 916 mikestorey  staff  29312 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.506Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_4
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-08902611-5zd9yhjk
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 914 mikestorey  staff  29248 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.584Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_0
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-354dfc90-yiorzrik
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 914 mikestorey  staff  29248 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.598Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_1
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-ed99140b-s_0etlmv
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 914 mikestorey  staff  29248 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.608Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_2
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-b0a70012-1s3g4i2l
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 914 mikestorey  staff  29248 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


### 2026-01-14T21:32:39.620Z | Exit Code: 0

**Stdout:**
```
Running SimpleRunbook
Test variable value: test_value_4
Current directory: /private/var/folders/2h/kn3qqgm55076h8w0tk79r1cm0000gn/T/runbook-exec-cfcea477-5b71o5gj
Listing files:
total 8
drwx------@   3 mikestorey  staff     96 Jan 14 16:32 .
drwx------@ 914 mikestorey  staff  29248 Jan 14 16:32 ..
-rwx------@   1 mikestorey  staff    195 Jan 14 16:32 temp.zsh
SimpleRunbook completed successfully

```


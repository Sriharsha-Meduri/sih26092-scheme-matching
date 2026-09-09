# KB/raw — Read-Only Source Snapshots

These files are byte-exact copies of the original source artifacts. They are
frozen inputs for reproducible KB transformations. NEVER edit them.

| Artifact | Bytes | SHA-256 (full) |
|---|---|---|
| `Master_DB.txt` | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| `SIH26092_Knowledge_Base_Source_Register.xlsx` | 10776 | 3e89c67beba75672b5031b3d565d48e6f0e1fef96ea9a66e8cd8f26b6ff08c3d |
| `SIH26092_Scheme_Master_KB.json` | 13546 | e6045072da5068c1cd5f0d2add4c71a3ef2b8d4ea4e6c5bbe0f4d9ef60bf20e6 |

## Original files (also read-only, untouched)
- `KB/Master DB.txt` (0 bytes — empty)
- `KB/SIH26092_Knowledge_Base_Source_Register.xlsx`
- `KB/SIH26092_Scheme_Master_KB.json`

`Master DB.txt` contains no data. It is preserved as-is per M0 decision B4
(disposition deferred; no modification/deletion without team consent).

## Verification
To verify a raw copy matches the original:

```
git hash-object KB/SIH26092_Scheme_Master_KB.json KB/raw/SIH26092_Scheme_Master_KB.json
```
(both lines must be identical)

All KB build scripts read from `KB/raw/` only.
# HOMEDANT USA — working rules

## The company OneDrive is read-only. No exceptions.

The Microsoft 365 connector reaches the Speedrack OneDrive, including
`01_사진 ~ 05_본사 관련 자료`. Those are the company's master design files and
photography. There is no second copy.

Having write permission is not permission. In that drive you may only:

- list folders (`sharepoint_folder_search`, `read_resource`)
- open and look at files (`read_resource`)
- search by name or content (`sharepoint_search`)

You may **never** delete, overwrite, move, rename, or create anything there.
That means `sharepoint_update_file`, `sharepoint_upload_file`,
`sharepoint_delete_item`, `sharepoint_move_item`, `sharepoint_rename_item`,
`sharepoint_copy_item` and `sharepoint_create_folder` are off limits for this
drive, whatever the reason and however safe the change looks.

If a change there seems necessary, say so and let Leo do it himself.

## The working copy of the photography

`scripts/sync_photos.ps1` runs on Leo's PC. It reads the master library and
writes downscaled copies into `assets/library/` in this repository, because
that is the only place a photograph can be opened as a file: this session can
look at OneDrive through the connector but cannot read bytes out of it, and
GitHub Actions cannot reach OneDrive at all. The original stays where it is,
untouched.

`해외영업3파트/업무/@업무/자동화/Image`, on Leo's own drive, is for finished
work going the other way — images this agent made. Never a copy of an original.

The repository is public, so `assets/library/` takes only what may be seen
outside: the script excludes competitor analysis, work in progress and
customer-specific artwork at the source.

## Confidential material

The repository is public. Pricing, margins, container volumes, competitor
analysis and buyer terms from the Lowe's vendor deck are never committed and
never published. Show organisers' logos and award badges go in only from the
official exhibitor or winner kit.

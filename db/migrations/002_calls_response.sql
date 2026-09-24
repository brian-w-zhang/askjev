-- Cached Jev responses (answers + usage only; full raw bodies live in data/calls/*.jsonl)
alter table calls add column if not exists response jsonb;

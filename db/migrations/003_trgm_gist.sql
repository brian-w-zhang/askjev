-- GiST trigram index so similarity search on longer queries stays fast (frontend search).
create index if not exists q_trgm_gist on questions using gist (text gist_trgm_ops);

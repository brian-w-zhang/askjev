-- Question ring layout (docs/07-ui.md): position of each question in its topic's ring, computed by `askjev layout`.
-- theta in [0,1): angle around the ring (similar questions adjacent); rho in [0,1]: position across the ring's width.
alter table questions add column if not exists layout_theta real;
alter table questions add column if not exists layout_rho real;

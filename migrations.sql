-- postgres
create table items (
	id SERIAL PRIMARY KEY,
	title VARCHAR(255) NOT NULL,
	category_id INTEGER NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC') NOT NULL,
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC') NOT NULL
);

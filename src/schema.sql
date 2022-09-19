CREATE TABLE IF NOT EXISTS works (
  tag_id INT NOT NULL,
  work_id INT NOT NULL,
  title TEXT NOT NULL,
  timestamp INT NOT NULL,
  PRIMARY KEY (tag_id, work_id) ON CONFLICT IGNORE
);

-- CREATE TABLE IF NOT EXISTS tags (
--   tag_id INT NOT NULL,
--   tag_name TEXT NOT NULL,
--   PRIMARY KEY (tag_id) ON CONFLICT IGNORE
-- );
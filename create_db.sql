create table user
(
    id        integer primary key,
    user_id   integer UNIQUE,
    user_name VARCHAR(35)
);

create table category
(
    id   integer primary key,
    name VARCHAR(255),
    user_id integer,
    FOREIGN KEY (user_id) REFERENCES user (user_id)
);

create table expense
(
    id            integer primary key,
    expense_value integer,
    created       datetime,
    category      integer,
    user_id          integer,
    FOREIGN KEY (category) REFERENCES category (codename),
    FOREIGN KEY (user_id) REFERENCES user (user_id)
);

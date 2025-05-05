create sequence credentials_id_seq;

alter sequence credentials_id_seq owner to postgres;

create table if not exists "user"
(
    id             bigint                         not null
        constraint user_pk
            primary key,
    is_bot         boolean          default false not null,
    first_name     varchar(64)                    not null,
    last_name      varchar(64),
    username       varchar(64),
    language_code  varchar(64),
    credentials_id integer
        constraint user_credentials_id_key
            unique,
    is_subscribed  boolean          default false not null,
    balance        double precision default 0.0   not null
)
    using ???;

alter table "user"
    owner to postgres;

create table if not exists chat
(
    name    varchar(128)         not null,
    user_id bigint               not null
        constraint chat_user_id_fk
            references "user",
    id      bigint               not null,
    active  boolean default true not null,
    constraint chats_pk
        primary key (id, user_id)
)
    using ???;

alter table chat
    owner to postgres;

create table if not exists theme
(
    id          serial
        constraint theme_pk
            primary key,
    name        varchar(64) not null,
    description text,
    user_id     bigint
        constraint theme_user_id_fk
            references "user",
    gpt         text        not null
)
    using ???;

alter table theme
    owner to postgres;

create table if not exists chat_theme
(
    chat_id  bigint not null,
    theme_id bigint not null
        constraint theme_fk
            references theme,
    user_id  bigint,
    constraint chat_theme_pk
        primary key (chat_id, theme_id),
    constraint chat_fk
        foreign key (chat_id, user_id) references chat
)
    using ???;

alter table chat_theme
    owner to postgres;

create table if not exists credentials
(
    id       integer default nextval('credentials_id_seq'::regclass) not null
        constraint credentials_pkey
            primary key,
    api_id   integer                                                 not null,
    api_hash varchar(255)                                            not null,
    phone    varchar(255)                                            not null,
    user_id  bigint                                                  not null
        constraint credentials_user_id_key
            unique
        constraint credentials_user_id_fkey
            references "user"
)
    using ???;

alter table credentials
    owner to postgres;

alter table "user"
    add constraint fk_credentials
        foreign key (credentials_id) references credentials;

create table if not exists message
(
    id              bigint                              not null
        constraint message_pk
            primary key,
    text            text                                not null,
    mentioned_id    bigint
        constraint message_mentioned_id_fk
            references message,
    chat_id         bigint                              not null,
    user_id         bigint                              not null,
    created_at      timestamp default CURRENT_TIMESTAMP not null,
    sender_id       bigint                              not null,
    theme_id        integer                             not null
        constraint message_theme_id_fk
            references theme,
    sender_username varchar,
    constraint message_chat_id_user_id_fk
        foreign key (chat_id, user_id) references chat
)
    using ???;

alter table message
    owner to postgres;

create table if not exists "order"
(
    id      serial
        constraint order_pk
            primary key,
    uuid    varchar(64)           not null,
    is_paid boolean default false not null,
    user_id bigint
        constraint order_user_id_fk
            references "user",
    amount  double precision      not null
)
    using ???;

alter table "order"
    owner to postgres;


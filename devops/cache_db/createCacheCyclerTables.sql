-- Table ExperimentCache --------------------------
create table if not exists ExperimentCache
(
    ExpID           mediumint       unsigned    not null,
    Name            varchar(30)                 not null,
    Description     varchar(250)                not null,
    DateCreation    datetime                    not null,
    DateBegin       datetime                    null,
    DateFinish      datetime                    null,
    Status          enum ('RUNNING', 'FINISHED', 'ERROR', 'PAUSED', 'QUEUED') not null,       -- RUNNING, FINISHED, ERROR, PAUSED, QUEUED
    CSID            mediumint       unsigned    not null,
    BatID           mediumint       unsigned    not null,
    ProfID          mediumint       unsigned    not null,

    constraint ExperimentCache_pk_1
        primary key (ExpID)
);


-- Table Alarm --------------------------
create table if not exists Alarm
(
    ExpID           mediumint       unsigned    not null,
    AlarmID         mediumint       unsigned    not null,
    Timestamp       datetime                    not null,
    Code            mediumint       unsigned    not null,
    Value           mediumint                   not null,

    constraint Alarm_pk_1
        primary key (ExpID, AlarmID),
    constraint Alarm_fk_1
        foreign key (ExpID) references ExperimentCache (ExpID)
);


-- Table StatusCache --------------------------
create table if not exists StatusCache
(
    StatusID        mediumint       unsigned    not null,
    ExpID           mediumint       unsigned    not null,
    DevID           mediumint       unsigned    not null,
    Timestamp       datetime                    not null,
    Status          enum ('OK', 'COMM_ERROR', 'INTERNAL_ERROR') not null,
    ErrorCode       smallint        unsigned    not null,

    constraint StatusCache_pk_1
        primary key (StatusID, ExpID),
    constraint StatusCache_fk_1
        foreign key (ExpID) references ExperimentCache (ExpID)
);


-- Table GenericMeasuresCache --------------------------
create table if not exists GenericMeasuresCache
(
    ExpID           mediumint       unsigned    not null,
    MeasID          int             unsigned    not null,
    Timestamp       datetime                    not null,
    InstrID         mediumint       unsigned    not null,
    Voltage         mediumint                   not null,
    Current         mediumint                   not null,
    Power           int                         not null,
    PowerMode       enum ('DISABLE', 'WAIT', 'CC_MODE', 'CV_MODE', 'CP_MODE') not null,

    constraint GenericMeasuresCache_pk_1
        primary key (ExpID, MeasID),
    constraint GenericMeasuresCache_fk_1
        foreign key (ExpID) references ExperimentCache (ExpID)
);


-- Table ExtendedMeasuresCache --------------------------
create table if not exists ExtendedMeasuresCache
(
    MeasID          int             unsigned    not null,
    ExpID           mediumint       unsigned    not null,
    UsedMeasID      mediumint       unsigned    not null,
    Value           mediumint                   not null,

    constraint ExtendedMeasuresCache_pk_1
        primary key (ExpID, UsedMeasID, MeasID),
    constraint ExtendedMeasuresCache_fk_1
        foreign key (ExpID, MeasID) references GenericMeasuresCache (ExpID, MeasID)
);

CREATE User 'basic_user'@'%' IDENTIFIED BY 'basic_user';
GRANT SELECT, SHOW VIEW ON wattrex_cache_db.* TO 'basic_user'@'%';
-- ALTER USER 'basic_user'@'%' IDENTIFIED WITH mysql_native_password BY 'basic_user';
FLUSH PRIVILEGES;

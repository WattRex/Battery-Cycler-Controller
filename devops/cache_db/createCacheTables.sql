-- Table Experiment --------------------------
create table if not exists Experiment
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

    constraint Experiment_pk_1
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
        foreign key (ExpID) references Experiment (ExpID)
);


-- Table Status --------------------------
create table if not exists Status
(
    StatusID        mediumint       unsigned    not null    auto_increment,
    ExpID           mediumint       unsigned    not null,
    DevID           mediumint       unsigned    not null,
    Timestamp       datetime                    not null,
    Status          enum ('OK', 'COMM_ERROR', 'INTERNAL_ERROR') not null,
    ErrorCode       smallint        unsigned    not null,

    constraint Status_pk_1
        primary key (StatusID, ExpID),
    constraint Status_fk_1
        foreign key (ExpID) references Experiment (ExpID)
);


-- Table GenericMeasures --------------------------
create table if not exists GenericMeasures
(
    ExpID           mediumint       unsigned    not null,
    MeasID          int             unsigned    not null,
    Timestamp       datetime                    not null,
    InstrID         mediumint       unsigned    not null,
    Voltage         mediumint                   not null,
    Current         mediumint                   not null,

    constraint GenericMeasures_pk_1
        primary key (ExpID, MeasID),
    constraint GenericMeasures_fk_1
        foreign key (ExpID) references Experiment (ExpID)
);


-- Table ExtendedMeasures --------------------------
create table if not exists ExtendedMeasures
(
    ExpID           mediumint       unsigned    not null,
    MeasType        mediumint       unsigned    not null,
    MeasID          int             unsigned    not null,
    Value           mediumint                   not null,

    constraint ExtendedMeasures_pk_1
        primary key (ExpID, MeasType, MeasID),
    constraint ExtendedMeasures_fk_1
        foreign key (ExpID, MeasID) references GenericMeasures (ExpID, MeasID)
);

CREATE User 'basic_user'@'%' IDENTIFIED BY 'basic_user';
GRANT SELECT, SHOW VIEW ON battery_experiments_manager_db.* TO 'basic_user'@'%';
-- ALTER USER 'basic_user'@'%' IDENTIFIED WITH mysql_native_password BY 'basic_user';
FLUSH PRIVILEGES;

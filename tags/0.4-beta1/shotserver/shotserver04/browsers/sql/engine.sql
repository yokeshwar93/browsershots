INSERT INTO "browsers_engine" ("id","name","maker") VALUES (1,'Gecko','Mozilla');
INSERT INTO "browsers_engine" ("id","name","maker") VALUES (2,'KHTML','KDE');
INSERT INTO "browsers_engine" ("id","name","maker") VALUES (3,'Opera','Opera');
INSERT INTO "browsers_engine" ("id","name","maker") VALUES (4,'AppleWebKit','Apple');
INSERT INTO "browsers_engine" ("id","name","maker") VALUES (5,'MSIE','Microsoft');
INSERT INTO "browsers_engine" ("id","name","maker") VALUES (6,'Netscape','Netscape');
INSERT INTO "browsers_engine" ("id","name","maker") VALUES (7,'Dillo','');
SELECT setval('browsers_engine_id_seq', (SELECT max("id") FROM "browsers_engine"));

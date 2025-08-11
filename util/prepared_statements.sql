DROP DATABASE IF EXISTS pstest; CREATE DATABASE pstest $$
CREATE PROCEDURE pstest.PS_CREATE()    BEGIN
  DECLARE a INT Default 1 ;
    WHILE a <= 10 DO
          SET @tbl = concat("tbl",a);
      SET @s = concat("CREATE TABLE ",@tbl," (id int auto_increment,rtext varchar(50), primary key(id)) ENGINE=InnoDB");
          PREPARE stmt1 FROM @s;
      EXECUTE stmt1;
      SET a=a+1;
   END WHILE;
END$$
CALL pstest.PS_CREATE()$$
CREATE PROCEDURE pstest.PS_INDEX()    BEGIN
  DECLARE a INT Default 1 ;
    WHILE a <= 10 DO
          SET @tbl = concat("tbl",a);
      SET @s = concat("CREATE INDEX itext ON ",@tbl," (rtext(10))");
          PREPARE stmt1 FROM @s;
      EXECUTE stmt1;
      SET a=a+1;
   END WHILE;
END $$
CALL pstest.PS_INDEX();$$
CREATE PROCEDURE pstest.PS_INSERT() BEGIN
  DECLARE create_start  INT DEFAULT 1;
  DECLARE insert_start INT DEFAULT 1;
  DECLARE create_count  INT DEFAULT 10;
  DECLARE insert_count INT DEFAULT 100;
    WHILE create_start <= create_count DO
      SET @tbl = concat("tbl",create_start);
      WHILE insert_start <= insert_count DO
        SELECT SUBSTRING(MD5(RAND()) FROM 1 FOR 50) INTO @str;
        SET @s = concat("INSERT INTO ",@tbl," (rtext) VALUES('",@str,"')");
        PREPARE stmt1 FROM @s;
        EXECUTE stmt1;
        SET insert_start = insert_start + 1;
      END WHILE;
      SET create_start=create_start+1;
          SET insert_start = 1;
    END WHILE;
END $$
CALL pstest.PS_INSERT();$$
CREATE PROCEDURE pstest.PS_DELETE(IN row_count INT)    BEGIN
  DECLARE a INT Default 1 ;
    WHILE a <= 10 DO
          SET @tbl = concat("tbl",a);
      SET @s = concat("DELETE FROM ",@tbl ," ORDER BY RAND() LIMIT ",row_count);
          PREPARE stmt1 FROM @s;
      EXECUTE stmt1;
      SET a=a+1;
   END WHILE;
END $$
CALL pstest.PS_DELETE(45) $$
CREATE PROCEDURE pstest.PS_ANALYZE()    BEGIN
  DECLARE a INT Default 1 ;
    WHILE a <= 10 DO
          SET @tbl = concat("tbl",a);
      SET @s = concat("ANALYZE TABLE ",@tbl);
          PREPARE stmt1 FROM @s;
      EXECUTE stmt1;
      SET a=a+1;
   END WHILE;
END $$
CALL pstest.PS_ANALYZE()$$
CALL pstest.PS_DELETE(35)$$
CREATE PROCEDURE pstest.PS_OPT_TABLE()    BEGIN
  DECLARE a INT Default 1 ;
    WHILE a <= 10 DO
          SET @tbl = concat("tbl",a);
      SET @s = concat("OPTIMIZE TABLE ",@tbl);
          PREPARE stmt1 FROM @s;
      EXECUTE stmt1;
      SET a=a+1;
   END WHILE;
END $$
CALL pstest.PS_OPT_TABLE()$$
CREATE PROCEDURE pstest.PS_UPDATE()    BEGIN
  DECLARE create_start  INT DEFAULT 1;
  DECLARE update_start INT DEFAULT 1;
  DECLARE create_count  INT DEFAULT 10;
  DECLARE update_count INT DEFAULT 50;
    WHILE create_start <= create_count DO
      SET @tbl = concat("tbl",create_start);
      WHILE update_start <= update_count DO
        SELECT SUBSTRING(MD5(RAND()) FROM 1 FOR 50) INTO @ustr;
        SET @s = concat("UPDATE ",@tbl ," SET rtext='",@ustr,"' ORDER BY RAND() LIMIT 1");
        PREPARE stmt1 FROM @s;
        EXECUTE stmt1;
        SET update_start = update_start + 1;
      END WHILE;
      SET create_start=create_start+1;
          SET update_start = 1;
    END WHILE;
END $$
CALL pstest.PS_UPDATE() $$
CREATE PROCEDURE pstest.PS_RPR_TABLE()    BEGIN
  DECLARE a INT Default 1 ;
    WHILE a <= 10 DO
          SET @tbl = concat("tbl",a);
      SET @s = concat("REPAIR TABLE ",@tbl);
          PREPARE stmt1 FROM @s;
      EXECUTE stmt1;
      SET a=a+1;
   END WHILE;
END $$
CALL pstest.PS_RPR_TABLE()$$
CREATE PROCEDURE pstest.PS_DROP_INDEX()    BEGIN
  DECLARE a INT Default 1 ;
    WHILE a <= 10 DO
          SET @tbl = concat("tbl",a);
      SET @s = concat("DROP INDEX itext ON ",@tbl);
          PREPARE stmt1 FROM @s;
      EXECUTE stmt1;
      SET a=a+1;
   END WHILE;
END $$
CALL pstest.PS_DROP_INDEX() $$
CREATE PROCEDURE pstest.PS_TRUNCATE()    BEGIN
  DECLARE a INT Default 1 ;
    WHILE a <= 10 DO
          SET @tbl = concat("tbl",a);
      SET @s = concat("TRUNCATE TABLE ",@tbl);
          PREPARE stmt1 FROM @s;
      EXECUTE stmt1;
      SET a=a+1;
   END WHILE;
END $$
CALL pstest.PS_TRUNCATE()$$
CREATE PROCEDURE pstest.PS_DROP_TABLE()    BEGIN
  DECLARE a INT Default 1 ;
    WHILE a <= 10 DO
          SET @tbl = concat("tbl",a);
      SET @s = concat("DROP TABLE ",@tbl);
          PREPARE stmt1 FROM @s;
      EXECUTE stmt1;
      SET a=a+1;
   END WHILE;
END $$
CALL pstest.PS_DROP_TABLE()$$
CREATE PROCEDURE pstest.PS_CREATE_USER()    BEGIN
  DECLARE a INT Default 1 ;
    WHILE a <= 10 DO
          SET @tuser = concat("testuser",a);
      SET @c = concat("DROP USER IF EXISTS ",@tuser,"@'%'");
      SET @s = concat("CREATE USER ",@tuser,"@'%' IDENTIFIED BY 'test123'");
      SET @t = concat("GRANT ALL ON *.* TO ",@tuser,"@'%'");
          PREPARE stmt1 FROM @c;
          PREPARE stmt2 FROM @s;
          PREPARE stmt3 FROM @t;
      EXECUTE stmt1;
      EXECUTE stmt2;
      EXECUTE stmt3;
      SET a=a+1;
   END WHILE;
END $$
CALL pstest.PS_CREATE_USER()$$

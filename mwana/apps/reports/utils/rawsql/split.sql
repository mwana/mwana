CREATE OR REPLACE FUNCTION split(text, text)
RETURNS text[] AS '
  DECLARE
    i int := 0;
    word text;
    result text := ''{'';
    result_arr text[];
  BEGIN
    LOOP
      i := i + 1;
      SELECT INTO word split_part($1, $2, i);
      IF word = '''' THEN
        EXIT;
      END IF;
      IF i > 1 THEN
        result := result || '',"'' || word || ''"'';
      ELSE
        result := result || ''"'' || word || ''"'';
      END IF;
    END LOOP;
    result := result || ''}'';
    result_arr := result;
    RETURN result_arr;
  END
' LANGUAGE 'plpgsql';
# Univerzální logický analyzátor a data logger
> Semestrální práce

Cílem semestrální práce je návrh a následná realizace hardware univerzálního logického analyzátoru a data loggeru, v rámci bakalářské práce v letním semestru, bude tato práce rozšířena o implementaci firmware a tvorbu uživatelského rozhraní pro PC.

Logický analyzátor je zařízení určené pro sledování a následnou analýzu průběhu
krátkodobých diskrétních signálů, data logger naopak slouží k dlouhodobému záznamu jak digitálních, tak i analogových dat a signálů.

Jako řídící jednotka celého systému je použit mikrokontrolér NXP s jádrem ARM Cortex-M3, 12bitovým A/D převodníkem a zařízením USB\,2.0 použitého pro komunikaci s PC. Pro generování časové značky jednotlivých záznamů slouží interní hodiny reálného času s externím krystalem. Součástí zařízení je i možnost připojení externího 24bitového A/D převodníku HX711. Pro uložení zaznamenaných dat je k dispozici SD karta bez filesystemu.

Kanály pro logický analyzátor a data logger jsou oddělené. Logický analyzátor má k dispozici osm kanálů, data logger je 4kanálový. Podpora 5\,V logiky na digitálních vstupech je prozatím zajištěna externě pomocí modulu převodníku napěťových úrovní.

Zařízení je možno napájet z USB, nebo lithium-iontového akumulátoru. Automatické přepínání napájení zajišťuje integrovaný obvod LM66200. Součástí napájecí části je i nabíjecí obvod s ochranou proti přebití, podvybití nebo zkratu akumulátoru.

## Logický analyzátor

Logický analyzátor je zařízení určené pro sledování a následnou analýzu průběhu diskrétních signálů (logických hodnot 0/1). Oproti osciloskopu umožňuje zachytit a zobrazit vícero signálů najednou.

## Data logger

Data logger je zařízení určené k automatickému měření a záznamu dat v čase. Používá se k dlouhodobému monitorování fyzikálních a elektrických veličin s přesnou časovou informací bez nutnosti trvalé obsluhy.

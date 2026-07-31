# Virtual-database
Virtual database used for PIL-DDA acquisition
This study proposes a comprehensive data analysis strategy that combines a virtual database with PIL (Progressive Injection Leaching) acquisition. This method uses a virtual database of flavonoids and triterpenoids as a precursor ion list, enabling targeted acquisition of compounds in a data-dependent acquisition mode, thus allowing for in-depth characterization of trace metabolites in natural products. Furthermore, this virtual database can also be used as a template for matching precursor ions to rapidly screen potential target compounds.
The input files for running the code include RAW.msp, Database.xlsx, and Virtual_databases_merge.xlsx, all of which are provided.

Currently the following parameters are fixed inside the script; you can modify them by editing the source code:
PPM tolerance – line return ppm_error <= 5, ppm_error (change 5 to your desired value).
Retention time cut‑off – line if rt <= 2: continue (alter the threshold).
Input file names – "RAW.msp", "Database.xlsx", "Virtual_databases_merge.xlsx" (search for these strings in the __main__ block).
Output file name – "Identification_match_result.xlsx".

configfile: "config.yaml"

rule all:
    input: "output/.audio_done"

rule fetch_taxonomy:
    output: touch("output/.taxonomy_done")
    shell: "python scripts/fetch_taxonomy.py"

rule process_audio:
    input: "output/.taxonomy_done"
    output: touch("output/.audio_done")
    shell: 'python scripts/process_audio.py --audio-dir "{config[audio_dir]}"'
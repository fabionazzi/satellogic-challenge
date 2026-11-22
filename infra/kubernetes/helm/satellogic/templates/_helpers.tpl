{{- define "satellogic.waitFor" -}}
- name: wait-for-deps
  image: {{ .image }}
  imagePullPolicy: Never
  command:
    - python
    - -c
    - |
      import socket, time
      for target in {{ .targets | toJson }}:
          host, port = target.split(":")
          while True:
              try:
                  socket.create_connection((host, int(port)), timeout=2).close()
                  break
              except OSError:
                  print(f"waiting for {target}", flush=True)
                  time.sleep(2)
{{- end }}

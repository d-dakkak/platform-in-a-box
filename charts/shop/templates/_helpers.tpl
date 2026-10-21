{{- define "shop.labels" -}}
app.kubernetes.io/part-of: shop
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "shop.image" -}}
{{- $root := index . 0 -}}
{{- $svc := index . 1 -}}
{{- with $root.Values.image.registry }}{{ . }}/{{ end }}{{ $svc.repository }}:{{ $root.Values.image.tag }}
{{- end -}}

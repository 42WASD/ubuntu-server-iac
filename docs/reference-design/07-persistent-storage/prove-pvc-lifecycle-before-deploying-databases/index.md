# prove PVC lifecycle before deploying databases

Test:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: storage-test
  namespace: dev-jya0
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: nvme-fast
  resources:
    requests:
      storage: 2Gi
```

Mount it:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: storage-test
  namespace: dev-jya0
spec:
  containers:
    - name: test
      image: busybox:1.36
      command: ["sh", "-c", "echo hello > /data/test.txt && sleep 3600"]
      resources:
        requests:
          cpu: 10m
          memory: 16Mi
        limits:
          cpu: 100m
          memory: 64Mi
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: storage-test
```

Check:

```bash
kubectl -n dev-jya0 get pvc,pv,pod
sudo lvs
```

Delete the Pod, recreate it, confirm the data remains.

Then delete the PVC and verify the selected reclaim policy behaves exactly as intended.

## Checkpoint 12

Do not deploy PostgreSQL/Harbor until:

```text
dynamic provision works
mount works
reboot works
expansion test works
reclaim behavior is understood
```

---

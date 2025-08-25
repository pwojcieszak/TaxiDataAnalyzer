#!/usr/bin/env sh
cat > transform_key.tf <<- EOM
resource "google_compute_project_metadata" "default" {
  metadata = {
    ssh-keys = <<EOF
EOM
echo -n "      $GCP_userID:" >> transform_key.tf
cat $GCP_privateKeyFile.pub >> transform_key.tf
cat >> transform_key.tf <<- EOM
    EOF
  }
}
EOM

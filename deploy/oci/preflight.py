"""Inventário OCI somente leitura, executado com o Python da OCI CLI."""
import argparse
import json
from pathlib import Path
import oci


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-file", required=True)
    parser.add_argument("--profile", required=True)
    args = parser.parse_args()
    config = oci.config.from_file(args.config_file, args.profile)
    signer = oci.auth.signers.SecurityTokenSigner(Path(config["security_token_file"]).read_text().strip(), oci.signer.load_private_key_from_file(config["key_file"]))
    def client(cls):
        return cls(config, signer=signer, timeout=(10, 45))
    def listing(method, **kwargs):
        return oci.pagination.list_call_get_all_results(method, **kwargs).data
    identity = client(oci.identity.IdentityClient)
    compute = client(oci.core.ComputeClient)
    tenancy = identity.get_tenancy(config["tenancy"]).data
    regions = listing(identity.list_region_subscriptions, tenancy_id=config["tenancy"])
    images = listing(compute.list_images, compartment_id=config["tenancy"], operating_system="Canonical Ubuntu", shape="VM.Standard.A1.Flex", sort_by="TIMECREATED", sort_order="DESC")
    active = listing(compute.list_instances, compartment_id=config["tenancy"])
    report = {
        "tenancy": tenancy.name, "region": config["region"],
        "regions": [{"region": r.region_name, "home": r.is_home_region} for r in regions],
        "active_instances": [{"name": i.display_name, "shape": i.shape} for i in active if i.lifecycle_state != "TERMINATED"],
        "images": [{"name": i.display_name, "version": i.operating_system_version, "id": i.id} for i in images],
        "planning_only": {"shape": "VM.Standard.A1.Flex", "ocpus": 1, "memory_gb": 6, "boot_gb": 47, "load_balancer": False, "capacity_verified": False, "zero_cost_guaranteed": False},
    }
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()

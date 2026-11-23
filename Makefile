CLUSTER     := satellogic
KIND_CONFIG := infra/kubernetes/kind-config.yaml
CHART       := infra/kubernetes/helm/satellogic
NAMESPACE   := satellogic
IMAGE_TAG   := local
SERVICES    := planner-service orbit-execution-service
SVC         ?= planner-app

.PHONY: up infra-up run check-tools cluster-up images status logs down demo test

up: infra-up run

infra-up: images

check-tools:
	@for tool in docker kind kubectl helm; do \
		command -v $$tool >/dev/null || { echo "Missing: $$tool"; missing=1; }; \
	done; \
	[ -z "$$missing" ] || { echo "See https://kind.sigs.k8s.io, https://kubernetes.io/docs/tasks/tools, https://helm.sh/docs/intro/install"; exit 1; }

cluster-up: check-tools
	@kind get clusters | grep -qx $(CLUSTER) || kind create cluster --config $(KIND_CONFIG)

images: cluster-up
	@for svc in $(SERVICES); do \
		docker build -t $$svc:$(IMAGE_TAG) -f $$svc/docker/Dockerfile $$svc && \
		kind load docker-image $$svc:$(IMAGE_TAG) --name $(CLUSTER) || exit 1; \
	done

run: cluster-up
	helm upgrade --install $(CLUSTER) $(CHART) -n $(NAMESPACE) --create-namespace \
		--set-string rollme=$$(date +%s) --force-conflicts --wait --timeout 5m

status:
	kubectl get pods,svc -n $(NAMESPACE)

logs:
	kubectl logs -f deployment/$(SVC) -n $(NAMESPACE) --all-containers --prefix

down:
	kind delete cluster --name $(CLUSTER)

demo:
	@python3 scripts/demo.py $(DEMO_ARGS)

test:
	docker build --target test -t planner-service:test -f planner-service/docker/Dockerfile planner-service
	docker run --rm planner-service:test

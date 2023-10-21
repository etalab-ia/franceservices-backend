## Administrer les ressources OUTSCALE

Il est possible d'administrer les ressources outscale via l'interface graphique cockpit ou via via le client outscale  **osc-cli** en *command line*

### Utiliser l'interface cockpit

UI pour administrer nos ressources cloud louées à Outscale

Lien : https://cockpit.outscale.com/#/region
Choisir la région euwest2 (ou secnumcloud euwest1 pour la deuxième machine disponible à partir du 1er novembre 2023)

Connexion avec datalab@modernisation.gouv.fr et le mot de passe correspondant.

#### Réserver une VM dans l'interface cockpit

Remarque : Il y a par exemple déjà une VM "sandbox" que nous avons créée et paramétrée le 9 octobre 2023 pour les entraînements de modèle, vous pouvez l'utiliser directement. Sinon, suivre la procédure ci-dessous

Remarque : le type de la VM est **tinav6.c20r80p1**


Dans l'onglet VM, créer ou relancer la VM de son choix.
Image conseillée : la dernière image d'Ubuntu 22.04 d'outscale, dont le code d'image outscale est "ami-cd8d714e"

Paramètres conseillés lors de la création d'une VM compatible avec une GPU A100 : cf capture d'écran ci-dessous (ou ci-jointe) 


![](https://storage.gra.cloud.ovh.net/v1/AUTH_0f20d409cb2a4c9786c769e2edec0e06/padnumerique/uploads/8331a0c8-18c0-401c-a8c1-ab49485dac67.png)

Si besoin d'installer les drivers nvidia sur cette image d'Ubuntu 22.04, les commandes sont 
```
sudo apt update
sudo apt install -y nvidia-driver-535
sudo apt install -y nvidia-cuda-toolkit nvidia-cuda-toolkit-gcc
```
Ne pas oublier :
1) d'attacher une IP externe à l'API - c'est à elle que l'on se connectera 
2) de rajouter une **keypair** qui permettra notamment de se connecter en SSH à la VM à cette IP
3) d'ajouter les IP de vos poste de travail au **security group**

#### Réserver un GPU dans l'interface cockpit

Dans l'onglet GPUde l'interface, réserver un autre GPU si besoin, puis l'associer à la VM. Attention, la VM créée devra avoir un CPU de génération 6 (cf capture d'écran plus haut)

Attention, la VM doit être au statut "stopped" au moment où l'on attache le GPU. Une fois que la carte GPU est attaché, l'on peut relancer la VM. De même, lorsque l'on détache la carte GPU après utilisation, l'on doit d'abord mettre la VM correspondante au statut stopped (attention à ne pas détacher la carte GPU de prod !).

#### Security group

Remarque : le security group actuel a le tag **sg-7c3739d4**. Vous pouvez l'utiliser ou en configurer un nouveau

Important : ajouter les IP de vos poste de travail au **security group**. Si vous utiliser des IP tournantes (partage de connexion ou autre), ne pas oublier de retirer vos anciennes IP du security group

## Le client **osc-cli**

Lien de la documentation de l'API : https://docs.outscale.com/api#3ds-outscale-api

La première étape est de configurer votre profil osc-cli (a priori dans ~/.osc/config.json) en y ajoutant notamment un "access key" et un "secret key".

Commande (à compléter) pour créer une VM depuis le terminal
```
osc-cli api CreateVms \
` --profile default \
  --ImageId ami-cd8d714e" \
  --SecurityGroupIds '["sg-4fcea312"]' \
  --KeypairName "[enter your keypair]" \
  --VmType "tinav6.c20r80p1" \
  --BlockDeviceMappings '[{"DeviceName": "/dev/sda1", "Bsu":{"VolumeSize": 200, "VolumeType": "gp2"}}]' \
```

Création d'une carte GPU
```
osc-cli api CreateFlexibleGpu --profile "default" \
  --ModelName "nvidia-a100" \
  --Generation "v6" \
  --SubregionName "eu-west-2a" \
  --DeleteOnVmDeletion True
```

Attacher la carte GPU
```
osc-cli api LinkFlexibleGpu --profile "default" \
  --FlexibleGpuId "enter it" \
  --VmId "enter it"
```

Détacher la carte GPU (ne pas oublier !)
```
osc-cli api UnlinkFlexibleGpu --profile "default" \
  --FlexibleGpuId "enter it"
```

# Contrato de plugins

## Forma del directorio

```text
plugins/
└── utility/
    └── example/
        ├── plugin.yaml
        └── entrypoint.py
```

## Manifiesto

```yaml
name: example-plugin
version: 1.0.0
type: utility
description: Extensión técnica de ejemplo
dependencies: []
entrypoint: entrypoint.py:create_plugin
```

El identificador resultante es `utility:example-plugin`. Los nombres y tipos deben empezar por una
letra minúscula y sólo pueden contener letras minúsculas, números, `_` o `-`.

`dependencies` es una lista de identificadores completos (`tipo:nombre`), por ejemplo:

```yaml
dependencies:
  - utility:foundation
```

Todas las dependencias deben estar presentes dentro del directorio de plugins configurado. El loader
rechaza duplicados, dependencias ausentes y ciclos antes de ejecutar cualquier entrypoint; los carga
en orden topológico. Esta regla sólo resuelve el orden local de inicialización: no instala paquetes
ni aplica resolución semántica de versiones.

## Entrypoint

El factory debe devolver un objeto con la propiedad `metadata`. Esta información debe coincidir
exactamente con el manifiesto.

```python
from quantlab.core.plugins import PluginMetadata


class ExamplePlugin:
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example-plugin",
            version="1.0.0",
            plugin_type="utility",
            description="Extensión técnica de ejemplo",
        )


def create_plugin() -> ExamplePlugin:
    return ExamplePlugin()
```

Los tipos `collector`, `feature`, `model` y `strategy` se introducirán sólo al implementar sus
respectivos casos de uso; este sprint no reserva lógica para ellos.

from typing import List, Union, Tuple, Dict
from enum import Enum
import torch
from torch import Tensor
from torch.nn import Module
from torch.utils.hooks import RemovableHandle

from ..helpers import tensor_sparsity, tensor_sample


__all__ = ['ASResultType', 'ASAnalyzerLayer', 'ASAnalyzerModule']


class ASResultType(Enum):
    inputs_sparsity = 'inputs_sparsity'
    inputs_sample = 'inputs_sample'
    outputs_sparsity = 'outputs_sparsity'
    outputs_sample = 'outputs_sample'


class ASAnalyzerLayer(object):
    def __init__(self, name: str, division: Union[None, int, Tuple[int, ...]],
                 track_inputs_sparsity: bool = False, track_outputs_sparsity: bool = False,
                 inputs_sample_size: int = 0, outputs_sample_size: int = 0,
                 enabled: bool = True):
        self._name = name
        self._division = division
        self._track_inputs_sparsity = track_inputs_sparsity
        self._track_outputs_sparsity = track_outputs_sparsity
        self._inputs_sample_size = inputs_sample_size
        self._outputs_sample_size = outputs_sample_size
        self._enabled = enabled
        self._connected = False

        self._inputs_sparsity = []  # type: List[Tensor]
        self._inputs_sample = []  # type: List[Tensor]
        self._outputs_sparsity = []  # type: List[Tensor]
        self._outputs_sample = []  # type: List[Tensor]
        self._module = None  # type: Module
        self._pre_hook_handle = None  # type: RemovableHandle
        self._hook_handle = None  # type: RemovableHandle

    def __del__(self):
        self._disable_hooks()

    def __str__(self):
        return ('name: {}, division: {}, track_inputs_sparsity: {}, track_outputs_sparsity: {}, '
                'inputs_sample_size: {}, outputs_sample_size: {}, enabled: {}'
                .format(self._name, self._division, self._track_inputs_sparsity, self._track_outputs_sparsity,
                        self._inputs_sample_size, self._outputs_sample_size, self._enabled))

    @property
    def name(self) -> str:
        return self._name

    @property
    def division(self) -> Union[None, int, Tuple[int, ...]]:
        return self._division

    @property
    def track_inputs_sparsity(self) -> bool:
        return self._track_inputs_sparsity

    @track_inputs_sparsity.setter
    def track_inputs_sparsity(self, value: bool):
        self._track_inputs_sparsity = value

    @property
    def track_outputs_sparsity(self) -> bool:
        return self._track_outputs_sparsity

    @track_outputs_sparsity.setter
    def track_outputs_sparsity(self, value: bool):
        self._track_outputs_sparsity = value

    @property
    def inputs_sample_size(self) -> int:
        return self._inputs_sample_size

    @inputs_sample_size.setter
    def inputs_sample_size(self, value: int):
        self._inputs_sample_size = value

    @property
    def outputs_sample_size(self) -> int:
        return self._outputs_sample_size

    @outputs_sample_size.setter
    def outputs_sample_size(self, value: int):
        self._outputs_sample_size = value

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def inputs_sparsity(self) -> List[Tensor]:
        return self.results(ASResultType.inputs_sparsity)

    @property
    def inputs_sparsity_mean(self) -> Tensor:
        return self.results_mean(ASResultType.inputs_sparsity)

    @property
    def inputs_sparsity_std(self) -> Tensor:
        return self.results_std(ASResultType.inputs_sparsity)

    @property
    def inputs_sparsity_max(self) -> Tensor:
        return self.results_max(ASResultType.inputs_sparsity)

    @property
    def inputs_sparsity_min(self) -> Tensor:
        return self.results_min(ASResultType.inputs_sparsity)

    @property
    def inputs_sample(self) -> List[Tensor]:
        return self.results(ASResultType.inputs_sample)

    @property
    def inputs_sample_mean(self) -> Tensor:
        return self.results_mean(ASResultType.inputs_sample)

    @property
    def inputs_sample_std(self) -> Tensor:
        return self.results_std(ASResultType.inputs_sample)

    @property
    def inputs_sample_max(self) -> Tensor:
        return self.results_max(ASResultType.inputs_sample)

    @property
    def inputs_sample_min(self) -> Tensor:
        return self.results_min(ASResultType.inputs_sample)

    @property
    def outputs_sparsity(self) -> List[Tensor]:
        return self.results(ASResultType.outputs_sparsity)

    @property
    def outputs_sparsity_mean(self) -> Tensor:
        return self.results_mean(ASResultType.outputs_sparsity)

    @property
    def outputs_sparsity_std(self) -> Tensor:
        return self.results_std(ASResultType.outputs_sparsity)

    @property
    def outputs_sparsity_max(self) -> Tensor:
        return self.results_max(ASResultType.outputs_sparsity)

    @property
    def outputs_sparsity_min(self) -> Tensor:
        return self.results_min(ASResultType.outputs_sparsity)

    @property
    def outputs_sample(self) -> List[Tensor]:
        return self.results(ASResultType.outputs_sample)

    @property
    def outputs_sample_mean(self) -> Tensor:
        return self.results_mean(ASResultType.outputs_sample)

    @property
    def outputs_sample_std(self) -> Tensor:
        return self.results_std(ASResultType.outputs_sample)
    
    @property
    def outputs_sample_max(self) -> Tensor:
        return self.results_max(ASResultType.outputs_sample)
    
    @property
    def outputs_sample_min(self) -> Tensor:
        return self.results_min(ASResultType.outputs_sample)

    def clear(self, specific_result_type: Union[None, ASResultType] = None):
        if specific_result_type is None or specific_result_type == ASResultType.inputs_sparsity:
            self._inputs_sparsity.clear()

        if specific_result_type is None or specific_result_type == ASResultType.inputs_sample:
            self._inputs_sample.clear()

        if specific_result_type is None or specific_result_type == ASResultType.outputs_sparsity:
            self._outputs_sparsity.clear()

        if specific_result_type is None or specific_result_type == ASResultType.outputs_sample:
            self._outputs_sample.clear()

    def enable(self):
        if not self._enabled:
            self._enabled = True
            self._enable_hooks()

    def disable(self):
        if self._enabled:
            self._enabled = False
            self._disable_hooks()

    def results(self, result_type: ASResultType) -> List[Tensor]:
        if result_type == ASResultType.inputs_sparsity:
            return self._inputs_sparsity

        if result_type == ASResultType.inputs_sample:
            return self._inputs_sample

        if result_type == ASResultType.outputs_sparsity:
            return self._outputs_sparsity

        if result_type == ASResultType.outputs_sample:
            return self._outputs_sample

        raise ValueError('result_type of {} is not supported'.format(result_type))

    def results_mean(self, result_type: ASResultType) -> Tensor:
        results = self.results(result_type)

        if not results:
            return torch.tensor([])

        return torch.mean(torch.cat(results), dim=0)

    def results_std(self, result_type: ASResultType) -> Tensor:
        results = self.results(result_type)

        if not results:
            return torch.tensor([])

        return torch.std(torch.cat(results), dim=0)
    
    def results_max(self, result_type: ASResultType) -> Tensor:
        results = self.results(result_type)
        
        if not results:
            return torch.tensor([])
        
        return torch.max(torch.cat(results))
    
    def results_min(self, result_type: ASResultType) -> Tensor:
        results = self.results(result_type)
        
        if not results:
            return torch.tensor([])
        
        return torch.min(torch.cat(results))

    def connect(self, module: Module):
        self._module = module
        self._connected = True

        if self.enabled:
            self._enable_hooks()

    def _set_results(self, result_type: ASResultType, layer_tens: Tensor):
        if result_type == ASResultType.inputs_sparsity:
            result = tensor_sparsity(layer_tens, dim=self.division)
            sparsities = result.cpu()
            self._inputs_sparsity.append(sparsities)
        elif result_type == ASResultType.outputs_sparsity:
            result = tensor_sparsity(layer_tens, dim=self.division)
            sparsities = result.cpu()
            self._outputs_sparsity.append(sparsities)
        elif result_type == ASResultType.inputs_sample:
            result = tensor_sample(layer_tens, self.inputs_sample_size, dim=self.division)
            samples = result.cpu()
            self._inputs_sample.append(samples)
        elif result_type == ASResultType.outputs_sample:
            result = tensor_sample(layer_tens, self.outputs_sample_size, dim=self.division)
            samples = result.cpu()
            self._outputs_sample.append(samples)
        else:
            raise ValueError('unrecognized result_type given {}'.format(result_type))

    def _enable_hooks(self):
        if not self._connected:
            return

        # set the layer when we are enabled
        layer = self._module
        layers = self.name.split('.')

        for lay in layers:
            layer = layer.__getattr__(lay)

        def _forward_pre_hook(_mod: Module, _inp: Union[Tensor, Tuple[Tensor]]):
            if not isinstance(_inp, Tensor):
                _inp = _inp[0]

            if self.track_inputs_sparsity:
                self._set_results(ASResultType.inputs_sparsity, _inp)

            if self.inputs_sample_size > 0:
                self._set_results(ASResultType.inputs_sample, _inp)

        self._pre_hook_handle = layer.register_forward_pre_hook(_forward_pre_hook)

        def _forward_hook(_mod: Module, _inp: Union[Tensor, Tuple[Tensor]], _out: Union[Tensor, Tuple[Tensor]]):
            if not isinstance(_out, Tensor):
                _out = _out[0]

            if self.track_outputs_sparsity:
                self._set_results(ASResultType.outputs_sparsity, _out)

            if self.outputs_sample_size > 0:
                self._set_results(ASResultType.outputs_sample, _out)

        self._hook_handle = layer.register_forward_hook(_forward_hook)

    def _disable_hooks(self):
        if self._pre_hook_handle is not None:
            self._pre_hook_handle.remove()
            self._pre_hook_handle = None

        if self._hook_handle is not None:
            self._hook_handle.remove()
            self._hook_handle = None


class ASAnalyzerModule(Module):
    def __init__(self, module: Module, layers: List[ASAnalyzerLayer]):
        super(ASAnalyzerModule, self).__init__()
        self.module = module
        self._layers = {}

        for layer in layers:
            if layer.name in self._layers:
                raise ValueError('duplicate layer {} found, can only have one entry per layer'.format(layer.name))

            layer.connect(self.module)
            self._layers[layer.name] = layer

    def __del__(self):
        self._layers.clear()

    @property
    def layers(self) -> Dict[str, ASAnalyzerLayer]:
        return self._layers

    def enable_layers(self):
        for lay in self._layers.values():
            lay.enable()

    def disable_layers(self):
        for lay in self._layers.values():
            lay.disable()

    def clear_layers(self, specific_result_type: Union[None, ASResultType] = None):
        for lay in self._layers.values():
            lay.clear(specific_result_type)

    def forward(self, *inp):
        self._model(*inp)
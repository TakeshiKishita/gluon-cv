# pylint: disable=line-too-long,too-many-lines,missing-docstring,arguments-differ,unused-argument
from mxnet import init
from mxnet.gluon import nn
from mxnet.gluon.nn import HybridBlock
from ...nn.block import Consensus
from ..inception import inception_v3

__all__ = ['inceptionv3_ucf101', 'ActionRecInceptionV3', 'ActionRecInceptionV3TSN']

def inceptionv3_ucf101(nclass=101, pretrained=True, tsn=False, partial_bn=True, num_segments=3, **kwargs):
    if tsn:
        model = ActionRecInceptionV3TSN(nclass=nclass, pretrained=pretrained, partial_bn=partial_bn, num_segments=num_segments)
    else:
        model = ActionRecInceptionV3(nclass=nclass, pretrained=pretrained, partial_bn=partial_bn)
    return model

class ActionRecInceptionV3(HybridBlock):
    r"""InceptionV3 model for video action recognition

    Parameters
    ----------
    nclass : int, number of classes
    pretrained : bool, load pre-trained weights or not

    Input: a single image
    Output: a single predicted action label
    """
    def __init__(self, nclass, pretrained=True, partial_bn=True, **kwargs):
        super(ActionRecInceptionV3, self).__init__()

        pretrained_model = inception_v3(pretrained=pretrained, partial_bn=partial_bn, **kwargs)
        self.features = pretrained_model.features
        def update_dropout_ratio(block):
            if isinstance(block, nn.basic_layers.Dropout):
                block._rate = 0.8
        self.apply(update_dropout_ratio)
        self.output = nn.Dense(units=nclass, in_units=2048, weight_initializer=init.Normal(sigma=0.001))
        self.output.initialize()

    def hybrid_forward(self, F, x):
        x = self.features(x)
        x = self.output(x)
        return x

class ActionRecInceptionV3TSN(HybridBlock):
    r"""InceptionV3 model with temporal segments for video action recognition

    Parameters
    ----------
    nclass : int, number of classes
    pretrained : bool, load pre-trained weights or not

    Input: N images from N segments in a single video
    Output: a single predicted action label
    """
    def __init__(self, nclass, pretrained=True, partial_bn=True, num_segments=3, **kwargs):
        super(ActionRecInceptionV3TSN, self).__init__()

        self.basenet = ActionRecInceptionV3(nclass=nclass, pretrained=pretrained, partial_bn=partial_bn)
        self.tsn_consensus = Consensus(nclass=nclass, num_segments=num_segments)

    def hybrid_forward(self, F, x):
        pred = self.basenet(x)
        consensus_out = self.tsn_consensus(pred)
        return consensus_out
